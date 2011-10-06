import pylab as pl
import pymc as mc
import pandas
import networkx as nx

def all_plots_for(model, vars, emp_priors, t):
    plot_one_type(model, vars, emp_priors, t)
    plot_one_ppc(vars, t)
    plot_one_effects(vars, t, model.hierarchy)
    plot_convergence_diag(vars)
    #pl.figtext(.5, .5, 'AM grouping: %s\niter=%d, burn=%d, thin=%d' % (prior_models[t].am_grouping, prior_models[t].iter, prior_models[t].burn, prior_models[t].thin),
    #         color='r', va='center', ha='center', fontsize=24)
    plot_hists(vars)

def all_plots(model, vars, emp_priors, posteriors):
    plot_fit(model, vars, emp_priors, posteriors)
    plot_effects(vars, model.hierarchy)
    for t in 'i r f p pf rr'.split():
        if 'p_obs' in vars[t]:
            plot_one_ppc(vars[t], t)
    plot_convergence_diag(vars)
    plot_hists(vars)

def plot_data_bars(df):
    """ Plot some data bars
    Input
    -----
    df : pandas.DataFrame with columns age_start, age_end, value
    """
    data_bars = zip(df['age_start'], df['age_end'], df['value'])

    # show at most 500 bars, to keep things fast
    if len(data_bars) > 500:
        import random
        data_bars = random.sample(data_bars, 500)

    # make lists of x and y points, faster than ploting each bar
    # individually
    x = []
    y = []
    for a_0i, a_1i, p_i in data_bars:
        x += [a_0i, a_1i, pl.nan]
        y += [p_i, p_i, pl.nan]

    pl.plot(x, y, 'ks-', mew=1, mec='w', ms=4)
    
def plot_fit(model, vars, emp_priors, posteriors):
    """ plot results of a fit"""
    pl.figure()
    ages = vars['i']['ages']  # not all data models have an ages key, but incidence always does
    for j, t in enumerate('i r f p rr pf'.split()):
        pl.subplot(2, 3, j+1)
        plot_data_bars(model.input_data[model.input_data['data_type'] == t])
        try:
            pl.plot(ages, vars[t]['mu_age'].stats()['mean'], 'k-', linewidth=2)
            pl.plot(ages, vars[t]['mu_age'].stats()['95% HPD interval'], 'k--')
        except TypeError:
            print 'Could not generate output statistics'
        if t in posteriors:
            pl.plot(ages, posteriors[t], color='b', linewidth=1)
        if t in emp_priors:
            if isinstance(emp_priors[t], mc.Node):
                pl.plot(ages, emp_priors[t].parents['mu'], color='r', linewidth=1)
            else:
                pl.plot(ages, emp_priors[t], color='r', linewidth=1)
        pl.title(t)

def plot_cur_params(vars):
    """ plot current value of rate parameters"""
    ages = vars['i']['ages']  # not all data models have an ages key, but incidence always does
    for j, t in enumerate('i r f p rr pf'.split()):
        pl.subplot(2, 3, j+1)
        pl.plot(ages, vars[t]['mu_age'].value, linewidth=2)


def plot_one_type(model, vars, emp_priors, t):
    """ plot results of fit for one data type only"""
    pl.figure()
    plot_data_bars(model.input_data[model.input_data['data_type'] == t])
    stats = vars['mu_age'].stats()
    if stats:
        pl.plot(vars['ages'], stats['mean'], 'k-', linewidth=2)
        pl.plot(vars['ages'], stats['95% HPD interval'], 'k--')
    if t in emp_priors:
        pl.plot(vars['ages'], emp_priors[t], color='r', linewidth=1)
    pl.title(t)

def plot_one_ppc(vars, t):
    """ plot data and posterior predictive check"""
    stats = vars['p_pred'].stats()
    if stats == None:
        return

    pl.figure()
    pl.title(t)


    x = vars['p_obs'].value.__array__()
    y = x - stats['quantiles'][50]
    yerr = [stats['quantiles'][50] - pl.atleast_2d(stats['95% HPD interval'])[:,0],
            pl.atleast_2d(stats['95% HPD interval'])[:,1] - stats['quantiles'][50]]
    pl.errorbar(x, y, yerr=yerr, fmt='ko', mec='w', capsize=0,
                label='Residual (Obs - Pred)')

    pl.legend(numpoints=1, fancybox=True, shadow=True)

    pl.grid()
    l,r,b,t = pl.axis()
    pl.hlines([0], l, r)
    pl.axis([0, r, b, t])

def plot_one_effects(vars, type, hierarchy):
    pl.figure()
    for i, (covariate, effect) in enumerate([['U', 'alpha'], ['X', 'beta']]):
        if isinstance(vars.get(effect), mc.Stochastic):
            pl.subplot(1, 2, i+1)
            pl.title('%s_%s' % (effect, type))

            stats = vars[effect].stats()
            if stats:
                cov_name = list(vars[covariate].columns)
                if effect == 'alpha':
                    index = sorted(pl.arange(len(cov_name)),
                                   key=lambda i: str(cov_name[i] in hierarchy and nx.shortest_path(hierarchy, 'all', cov_name[i]) or cov_name[i]))
                elif effect == 'beta':
                    index = pl.arange(len(cov_name))

                x = pl.atleast_1d(stats['mean'])
                y = pl.arange(len(x))

                xerr = pl.array([x - pl.atleast_2d(stats['95% HPD interval'])[:,0],
                                 pl.atleast_2d(stats['95% HPD interval'])[:,1] - x])
                pl.errorbar(x[index], y[index], xerr=xerr[:, index], fmt='bs', mec='w')

                l,r,b,t = pl.axis()
                pl.vlines([0], b-.5, t+.5)
                pl.hlines(y, l, r, linestyle='dotted')
                pl.xticks([l, 0, r])
                pl.yticks([])
                for i in index:
                    spaces = cov_name[i] in hierarchy and len(nx.shortest_path(hierarchy, 'all', cov_name[i])) or 0
                    pl.text(l, y[i], '%s%s' % (' * '*spaces, cov_name[i]), va='center', ha='left')
                pl.axis([l, r, -.5, t+.5])

def plot_convergence_diag(vars):
    """ plot autocorrelation for all stochs in a dict or dict of dicts"""
    pl.figure()

    # count number of stochastics in model
    cells = 0
    stochs = []
    for k in vars.keys():
        # handle dicts and dicts of dicts by making a list of nodes
        if isinstance(vars[k], dict):
            nodes = vars[k].values()
        else:
            nodes = [vars[k]]

        # handle lists of stochs
        for n in nodes:
            if isinstance(n, list):
                nodes += n

        for n in nodes:
            if isinstance(n, mc.Stochastic) and not n.observed:
                trace = n.trace()
                if len(trace) > 0:
                    stochs.append(n)
                    cells += len(pl.atleast_1d(n.value))

    # for each stoch, make an autocorrelation plot for each dimension
    rows = pl.floor(pl.sqrt(cells))
    cols = pl.ceil(cells/rows)

    tile = 1
    for s in sorted(stochs, key=lambda s: s.__name__):
        trace = s.trace()
        if len(trace.shape) == 1:
            trace = trace.reshape((len(trace), 1))
        for d in range(len(pl.atleast_1d(s.value))):
            pl.subplot(rows, cols, tile)
            pl.acorr(pl.atleast_2d(trace)[:, d], normed=True, detrend=pl.mlab.detrend_mean, maxlags=50)
            pl.xticks([])
            pl.yticks([])
            l,r,b,t = pl.axis()
            pl.axis([-10, r, -.1, 1.1])
            pl.title('\n\n%s[%d]'%(s.__name__, d), va='top', ha='center', fontsize=8)

            tile += 1
    pl.subplots_adjust(0,0,1,1,0,0)
    
    
def plot_hists(vars):
    """ plot histograms for all stochs in a dict or dict of dicts"""
    pl.figure()

    # count number of stochastics in model
    cells = 0
    stochs = []
    additional_vars = []
    for k in vars.keys():
        # handle dicts and dicts of dicts by making a list of nodes
        if isinstance(vars[k], dict):
            nodes = vars[k].values()
        else:
            nodes = [vars[k]]

        # handle lists of stochs
        for n in nodes:
            if isinstance(n, list):
                nodes += n

        for n in nodes:
            if isinstance(n, mc.Stochastic) and not n.observed:
                trace = n.trace()
                if len(trace) > 0:
                    stochs.append(n)
                    cells += len(pl.atleast_1d(n.value))

            if isinstance(n, mc.Potential) or \
                    (isinstance(n, mc.Stochastic) and n.observed):
                additional_vars.append(n)

    # for each stoch, make plot for each dimension
    rows = pl.floor(pl.sqrt(cells))
    cols = pl.ceil(cells/rows)

    tile = 1
    for s in sorted(stochs, key=lambda s: s.__name__):
        trace = s.trace()
        if len(trace.shape) == 1:
            trace = trace.reshape((len(trace), 1))

        for d in range(len(pl.atleast_1d(s.value))):
            pl.subplot(rows, cols, tile)

            # if trace.shape[1] == 1:
            #     # plot marginal distribution for just this stoch
            #     m = mc.MAP([s] + additional_vars)
            #     p_vals = pl.arange(min(trace),max(trace),(max(trace)-min(trace))/10)
            #     f_vals = pl.array([pl.exp(-m.func(p)) for p in p_vals])
            #     pl.plot(p_vals, pl.exp(f_vals - max(f_vals)))

            pl.hist(pl.atleast_2d(trace)[:, d], histtype='stepfilled', normed=True)
            pl.yticks([])
            ticks, labels = pl.xticks()
            pl.xticks(ticks[1:6:2], fontsize=8)
            pl.title('\n\n%s[%d]'%(s.__name__, d), va='top', ha='center', fontsize=8)


            tile += 1
    pl.subplots_adjust(0,.1,1,1,0,.2)
    
    