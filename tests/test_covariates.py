""" Test covariate model

These tests are use randomized computation, so they might fail
occasionally due to stochastic variation
"""

# matplotlib will open windows during testing unless you do the following
import matplotlib
matplotlib.use("AGG")

# add to path, to make importing possible
import sys
sys.path += ['.', '..']

import pylab as pl
import pymc as mc
import networkx as nx
import pandas

import data
import rate_model
import age_pattern
import covariate_model
reload(covariate_model)

def test_covariate_model_sim_no_hierarchy():
    # simulate normal data
    hierarchy = nx.DiGraph()
    hierarchy.add_node('all')

    X = mc.rnormal(0., 1.**2, size=(128,3))
    beta_true = [-.1, .1, .2]
    Y_true = pl.dot(X, beta_true)

    pi_true = pl.exp(Y_true)
    sigma_true = .01

    p = mc.rnormal(pi_true, 1./sigma_true**2.)

    data = pandas.DataFrame(dict(value=p, x_0=X[:,0], x_1=X[:,1], x_2=X[:,2]))
    data['area'] = 'all'
    data['sex'] = 'total'
    data['year_start'] = 2000
    data['year_end'] = 2000

    # create model and priors
    vars = {}
    vars.update(covariate_model.mean_covariate_model('test', 1, data, hierarchy, 'all'))
    vars.update(rate_model.normal_model('test', vars['pi'], 0., p, sigma_true))

    # fit model
    mc.MAP(vars).fit(method='fmin_powell', verbose=1)
    m = mc.MCMC(vars)
    m.use_step_method(mc.AdaptiveMetropolis, [m.beta])
    m.sample(20000, 10000, 10)

    # compare estimate to ground truth (skip endpoints, because they are extra hard to get right)
    assert pl.allclose(m.beta.stats()['mean'], beta_true, rtol=.2)
    lb, ub = m.beta.stats()['95% HPD interval'].T
    assert pl.mean((lb <= beta_true) & (beta_true <= ub)) > .5


def test_covariate_model_sim_w_hierarchy():
    n = 50

    # setup hierarchy
    hierarchy = nx.DiGraph()
    hierarchy.add_node('all')
    hierarchy.add_edge('all', 'USA', weight=.1)
    hierarchy.add_edge('all', 'CAN', weight=.1)

    # simulate normal data
    area_list = pl.array(['all', 'USA', 'CAN'])
    area = area_list[mc.rcategorical([.3, .3, .4], n)]

    sex_list = pl.array(['male', 'female', 'total'])
    sex = sex_list[mc.rcategorical([.3, .3, .4], n)]

    year = pl.array(mc.runiform(1990, 2010, n), dtype=int)
        
    alpha_true = dict(all=0., USA=.1, CAN=-.2)

    pi_true = pl.exp([alpha_true[a] for a in area])
    sigma_true = .01

    p = mc.rnormal(pi_true, 1./sigma_true**2.)

    data = pandas.DataFrame(dict(value=p, area=area, sex=sex, year_start=year, year_end=year))

    # create model and priors
    vars = {}
    vars.update(covariate_model.mean_covariate_model('test', mu=1, data=data, hierarchy=hierarchy, root='all'))
    vars.update(rate_model.normal_model('test', vars['pi'], 0., p, sigma_true))

    # fit model
    mc.MAP(vars).fit(method='fmin_powell', verbose=1)
    m = mc.MCMC(vars)
    #m.use_step_method(mc.AdaptiveMetropolis, m.alpha)
    m.sample(20000, 10000, 10)

    # compare estimate to ground truth (skip endpoints, because they are extra hard to get right)
    assert pl.allclose(m.alpha.stats()['mean'],
                       [0., 0., alpha_true[m.U.columns[2]], alpha_true[m.U.columns[3]]],
                       atol=.3)


# TODO: test covariates for predicting heterogeneity

if __name__ == '__main__':
    import nose
    nose.runmodule()
    
