# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import numpy as np
from plum import Dispatcher
from scipy.stats import multivariate_normal
from lab import B

from stheno.kernel import EQ, RQ, ScaledKernel
from stheno.mean import TensorProductMean, ZeroMean, ScaledMean
from stheno.random import Normal, GPPrimitive, Normal1D
from stheno.matrix import UniformlyDiagonal, Diagonal, dense
# noinspection PyUnresolvedReferences
from . import eq, neq, lt, le, ge, gt, raises, call, ok, eprint, allclose

dispatch = Dispatcher()


def test_corner_cases():
    yield raises, NotImplementedError, lambda: (Normal(np.eye(1)) +
                                                GPPrimitive(EQ()))
    yield eq, repr(GPPrimitive(EQ())), str(GPPrimitive(EQ()))


def test_normal():
    mean = np.random.randn(3, 1)
    chol = np.random.randn(3, 3)
    var = chol.dot(chol.T)

    dist = Normal(var, mean)
    dist_sp = multivariate_normal(mean[:, 0], var)

    # Test second moment.
    yield ok, allclose(dist.m2(), var + mean.dot(mean.T))

    # Test `logpdf` and `entropy`.
    x = np.random.randn(3, 10)
    yield ok, allclose(dist.logpdf(x), dist_sp.logpdf(x.T)), 'logpdf'
    yield ok, allclose(dist.entropy(), dist_sp.entropy()), 'entropy'

    # Test KL with Monte Carlo estimate.
    mean2 = np.random.randn(3, 1)
    chol2 = np.random.randn(3, 3)
    var2 = chol2.dot(chol2.T)
    dist2 = Normal(var2, mean2)
    samples = dist.sample(50000)
    kl_est = np.mean(dist.logpdf(samples)) - np.mean(dist2.logpdf(samples))
    kl = dist.kl(dist2)
    yield ok, np.abs(kl_est - kl) / np.abs(kl) < 5e-2, 'kl samples'

    # Check a diagonal normal and dense normal.
    mean = np.random.randn(3, 1)
    var_diag = np.random.randn(3) ** 2
    var = np.diag(var_diag)
    dist1 = Normal(var, mean)
    dist2 = Normal(Diagonal(var_diag), mean)
    samples = dist1.sample(100)
    yield ok, allclose(dist1.logpdf(samples),
                       dist2.logpdf(samples)), 'logpdf'
    yield ok, allclose(dist1.entropy(), dist2.entropy()), 'entropy'
    yield ok, allclose(dist1.kl(dist2), 0.), 'kl 1'
    yield ok, allclose(dist1.kl(dist1), 0.), 'kl 2'
    yield ok, allclose(dist2.kl(dist2), 0.), 'kl 3'
    yield ok, allclose(dist2.kl(dist1), 0.), 'kl 4'
    yield le, dist1.w2(dist1), 5e-4, 'w2 1'
    yield le, dist1.w2(dist2), 5e-4, 'w2 2'
    yield le, dist2.w2(dist1), 5e-4, 'w2 3'
    yield le, dist2.w2(dist2), 5e-4, 'w2 4'

    # Check a uniformly diagonal normal and dense normal.
    mean = np.random.randn(3, 1)
    var_diag_scale = np.random.randn() ** 2
    var = np.eye(3) * var_diag_scale
    dist1 = Normal(var, mean)
    dist2 = Normal(UniformlyDiagonal(var_diag_scale, 3), mean)
    samples = dist1.sample(100)
    yield ok, allclose(dist1.logpdf(samples),
                       dist2.logpdf(samples)), 'logpdf'
    yield ok, allclose(dist1.entropy(), dist2.entropy()), 'entropy'
    yield ok, allclose(dist1.kl(dist2), 0.), 'kl 1'
    yield ok, allclose(dist1.kl(dist1), 0.), 'kl 2'
    yield ok, allclose(dist2.kl(dist2), 0.), 'kl 3'
    yield ok, allclose(dist2.kl(dist1), 0.), 'kl 4'
    yield le, dist1.w2(dist1), 5e-4, 'w2 1'
    yield le, dist1.w2(dist2), 5e-4, 'w2 2'
    yield le, dist2.w2(dist1), 5e-4, 'w2 3'
    yield le, dist2.w2(dist2), 5e-4, 'w2 4'

    # Test sampling and dtype conversion.
    dist = Normal(3 * np.eye(200, dtype=np.integer))
    yield le, np.abs(np.std(dist.sample(1000)) ** 2 - 3), 5e-2, 'full'
    yield le, np.abs(np.std(dist.sample(1000, noise=2)) ** 2 - 5), 5e-2, \
          'full 2'

    dist = Normal(Diagonal(3 * np.ones(200, dtype=np.integer)))
    yield le, np.abs(np.std(dist.sample(1000)) ** 2 - 3), 5e-2, 'diag'
    yield le, np.abs(np.std(dist.sample(1000, noise=2)) ** 2 - 5), 5e-2, \
          'diag 2'

    dist = Normal(UniformlyDiagonal(3, 200))
    yield le, np.abs(np.std(dist.sample(1000)) ** 2 - 3), 5e-2, 'unif'
    yield le, np.abs(np.std(dist.sample(1000, noise=2)) ** 2 - 5), 5e-2, \
          'unif 2'


def test_normal_1d():
    # Test broadcasting.
    d = Normal1D(1, 0)
    yield eq, type(d.var), UniformlyDiagonal
    yield eq, B.shape(d.var), (1, 1)
    yield eq, B.shape(d.mean), (1, 1)

    d = Normal1D(1, [0, 0, 0])
    yield eq, type(d.var), UniformlyDiagonal
    yield eq, B.shape(d.var), (3, 3)
    yield eq, B.shape(d.mean), (3, 1)

    d = Normal1D([1, 2, 3], 0)
    yield eq, type(d.var), Diagonal
    yield eq, B.shape(d.var), (3, 3)
    yield eq, B.shape(d.mean), (3, 1)

    d = Normal1D([1, 2, 3], [0, 0, 0])
    yield eq, type(d.var), Diagonal
    yield eq, B.shape(d.var), (3, 3)
    yield eq, B.shape(d.mean), (3, 1)

    d = Normal1D(1)
    yield eq, type(d.var), UniformlyDiagonal
    yield eq, B.shape(d.var), (1, 1)
    yield eq, B.shape(d.mean), (1, 1)

    d = Normal1D([1, 2, 3])
    yield eq, type(d.var), Diagonal
    yield eq, B.shape(d.var), (3, 3)
    yield eq, B.shape(d.mean), (3, 1)

    yield raises, ValueError, lambda: Normal1D(np.eye(3))
    yield raises, ValueError, lambda: Normal1D(np.eye(3), 0)
    yield raises, ValueError, lambda: Normal1D(1, np.ones((3, 1)))
    yield raises, ValueError, lambda: Normal1D([1, 2], np.ones((3, 1)))


def test_normal_arithmetic():
    mean = np.random.randn(3, 1)
    chol = np.random.randn(3, 3)
    var = chol.dot(chol.T)
    dist = Normal(var, mean)

    mean = np.random.randn(3, 1)
    chol = np.random.randn(3, 3)
    var = chol.dot(chol.T)
    dist2 = Normal(var, mean)

    A = np.random.randn(3, 3)
    a = np.random.randn(1, 3)
    b = 5.
    yield ok, allclose((dist.rmatmul(a)).mean,
                       dist.mean.dot(a)), 'mean mul'
    yield ok, allclose((dist.rmatmul(a)).var,
                       a.dot(dense(dist.var)).dot(a.T)), 'var mul'
    yield ok, allclose((dist.lmatmul(A)).mean,
                       A.dot(dist.mean)), 'mean rmul'
    yield ok, allclose((dist.lmatmul(A)).var,
                       A.dot(dense(dist.var)).dot(A.T)), 'var rmul'
    yield ok, allclose((dist * b).mean, dist.mean * b), 'mean mul 2'
    yield ok, allclose((dist * b).var, dist.var * b ** 2), 'var mul 2'
    yield ok, allclose((b * dist).mean, dist.mean * b), 'mean rmul 2'
    yield ok, allclose((b * dist).var, dist.var * b ** 2), 'var rmul 2'
    yield raises, NotImplementedError, lambda: dist.__mul__(dist)
    yield raises, NotImplementedError, lambda: dist.__rmul__(dist)
    yield ok, allclose((dist + dist2).mean,
                       dist.mean + dist2.mean), 'mean sum'
    yield ok, allclose((dist + dist2).var,
                       dist.var + dist2.var), 'var sum'
    yield ok, allclose((dist.__add__(b)).mean, dist.mean + b), 'mean add'
    yield ok, allclose((dist.__radd__(b)).mean, dist.mean + b), 'mean radd'


@dispatch(Normal, Normal)
def close(n1, n2):
    return allclose(n1.mean, n2.mean) and allclose(n1.var, n2.var)


def test_gp_construction():
    k = EQ()
    m = TensorProductMean(lambda x: x ** 2)

    p = GPPrimitive(k)
    yield eq, type(p.mean), ZeroMean

    p = GPPrimitive(k, 5)
    yield eq, type(p.mean), ScaledMean

    p = GPPrimitive(k, m)
    yield eq, type(p.mean), TensorProductMean

    p = GPPrimitive(5)
    yield eq, type(p.kernel), ScaledKernel


def test_gp():
    # Check finite-dimensional distribution construction.
    k = EQ()
    m = TensorProductMean(lambda x: x ** 2)
    p = GPPrimitive(k, m)
    x = np.random.randn(10, 1)

    yield ok, close(Normal(k(x), m(x)), p(x))

    # Check conditioning.
    sample = p(x).sample()
    post = p.condition(x, sample)

    mu, lower, upper = post.predict(x)
    yield ok, allclose(mu[:, None], sample), 'mean at known points'
    yield ok, np.all(upper - lower < 1e-5), 'sigma at known points'

    mu, lower, upper = post.predict(x + 20.)
    sig = (upper - lower) / 4
    yield ok, allclose(mu[:, None], m(x + 20.)), 'mean at unknown points'
    yield ok, allclose(sig ** 2,
                       B.diag(k(x + 20.))), 'variance at unknown points'

    # Check that conditioning is independent of order.
    x1 = np.random.randn(5, 2)
    x2 = np.random.randn(5, 2)
    y1 = np.random.randn(5, 1)
    y2 = np.random.randn(5, 1)
    x_test = np.random.randn(5, 2)
    x = np.concatenate((x1, x2), axis=0)
    y = np.concatenate((y1, y2), axis=0)

    d1 = p.condition(x1, y1).condition(x2, y2)(x_test)
    d2 = p.condition(x2, y2).condition(x1, y1)(x_test)
    d3 = p.condition(x, y)(x_test)

    yield ok, close(d1, d2), 'conditioning order'
    yield ok, close(d1, d3)
    yield ok, close(d2, d3)


def test_gp_arithmetic():
    x = np.random.randn(10, 2)

    gp1 = GPPrimitive(EQ())
    gp2 = GPPrimitive(RQ(1e-1))

    yield raises, NotImplementedError, lambda: gp1 * gp2
    yield raises, NotImplementedError, lambda: gp1 + Normal(np.eye(3))
    yield ok, close((5. * gp1)(x), 5. * gp1(x)), 'mul'
    yield ok, close((gp1 + gp2)(x), gp1(x) + gp2(x)), 'add'
    yield ok, close((gp1 + 1.)(x), gp1(x) + 1.), 'add 2'


def test_gp_stretching():
    m = TensorProductMean(lambda x: x ** 2)
    gp = GPPrimitive(EQ(), m)

    yield eq, str(gp.stretch(1)), 'GP(EQ() > 1, <lambda> > 1)'


def test_gp_select():
    m = TensorProductMean(lambda x: x ** 2)
    gp = GPPrimitive(EQ(), m)

    yield eq, str(gp.select(1)), 'GP(EQ() : [1], <lambda> : [1])'
    yield eq, str(gp.select(1, 2)), 'GP(EQ() : [1, 2], <lambda> : [1, 2])'


def test_gp_shifting():
    m = TensorProductMean(lambda x: x ** 2)
    gp = GPPrimitive(EQ(), m)

    yield eq, str(gp.shift(1)), 'GP(EQ(), <lambda> shift 1)'


def test_gp_transform():
    m = TensorProductMean(lambda x: x ** 2)
    gp = GPPrimitive(EQ(), m)

    yield eq, str(gp.transform(lambda x, c: x)), \
          'GP(EQ() transform <lambda>, <lambda> transform <lambda>)'


def test_gp_derivative():
    m = TensorProductMean(lambda x: x ** 2)
    gp = GPPrimitive(EQ(), m)

    yield eq, str(gp.diff(1)), 'GP(d(1) EQ(), d(1) <lambda>)'
