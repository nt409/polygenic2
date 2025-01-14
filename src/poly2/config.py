"""
This file sets up the parameters for the polygenic model

Two setups:
- Config (one or two traits valid here)
- ConfigMixture (two fungicides)


And functions:
- print_str_repr
- remove_host_attrs_from_config
- get_asymptote_config
"""

import copy
import numpy as np
import pandas as pd

from poly2.consts import (
    ALL_BETAS,
    DEFAULT_BETA,
    DEFAULT_I0,
    DEFAULT_MUTATION_SCALE,
    MUTATION_PROP
)


class Config:
    def __init__(
        self,
        #
        type=None,
        #
        sprays=None,
        host_on=None,
        #
        n_k=50,
        n_l=50,
        #
        n_iterations=None,
        n_years=15,
        #
        replace_cultivars=False,
        #
        mutation_proportion=MUTATION_PROP,
        mutation_scale_host=DEFAULT_MUTATION_SCALE,
        mutation_scale_fung=DEFAULT_MUTATION_SCALE,
        #
        decay_rate=None,
        asymptote=None,
        #
        dose=None,
        #
        verbose=True,
    ):
        """Config for polygenic model

        There are various ways we want to run the model:
        - single run
        - multiple run (varying disease pressure)

        Then specify tactics for single/multi runs via sprays and host on

        Specify the scenario with disease pressure and cultivar

        Parameters
        ----------
        type : str, optional
            Can be:
            - 'single'
            - 'multi'
            by default None which gives 'single'

        sprays : list of ints, optional
            will be passed into itertools.product with host_on
            e.g.
            [0,1,2,3] will check all spray possibilities
            by default None

        host_on : list of booleans, optional
            will be passed into itertools.product with sprays
            e.g.
            [False] will run without host protection
            [True] will run with host protection
            [False, True] will run both
            by default None

        n_k : int, optional
            Number controlling fungicide distribution discretisation
            Suggest XX for final run and YY for quick run
            By default 50

        n_l : int, optional
            Number controlling fungicide distribution discretisation
            Suggest XX for final run and YY for quick run
            By default 50

        n_iterations : int, optional
            number of iterations if running multi, by default None

        n_years : int, optional
            number of years to run the model, by default 25

        replace_cultivars : bool, array, optional
            whether or not to replace cultivars, by default False.
            If want to, specify an array of booleans for whether to replace at
            of year 0, 1, ... N-1

        mutation_proportion : float, optional
            Proportion of pathogen population that mutates.
            Between 0 and 1, by default 0

        mutation_scale_fung : float, optional
            Scaling for mutation (assume gaussian dispersal), by default 0

        mutation_scale_host : float, optional
            Scaling for mutation (assume gaussian dispersal), by default 0

        decay_rate : float, optional
            Fungicide decay rate if want =/= default, by default None

        asymptote : float, optional
            Fungicide asymptote if want =/= default, in [0,1], by default None

        dose : float, optional
            use dose * np.ones(n_years), by default None
            If None, use np.ones(n_years)

        verbose : bool, optional
            whether to print out summary of config, by default True

        Examples
        --------
        >>>single = Config(
        ... sprays=[2],
        ... host_on=[False],
        ... n_k=100,
        ... n_l=100
        ... )
        >>>multi = Config(
        ... type='multi',
        ... sprays=[0,2],
        ... host_on=[False],
        ... n_iterations=10
        ... )
        """

        self.n_years = n_years

        #
        #
        # STRATEGY
        self.sprays = sprays

        # used in poly2.run
        self.fungicide_mixture = False

        self.n_k = n_k
        self.n_l = n_l

        self.decay_rate = decay_rate
        self.asymptote = asymptote

        if dose is None:
            self.doses = np.ones(self.n_years)
        else:
            self.doses = dose * np.ones(self.n_years)

        self.host_on = host_on

        if replace_cultivars is not False:
            self.replace_cultivars = replace_cultivars
        else:
            self.replace_cultivars = None

        #
        #
        # PATHOGEN
        self.mutation_proportion = mutation_proportion

        self.mutation_scale_host = mutation_scale_host
        self.mutation_scale_fung = mutation_scale_fung

        fit = pd.read_csv('../data/fitted.csv')

        assert len((
            fit.loc[(
                (np.isclose(fit.mutation_prop, mutation_proportion)) &
                (np.isclose(fit.mutation_scale_fung, mutation_scale_fung)) &
                (np.isclose(fit.mutation_scale_host, mutation_scale_host))
            )]
        )) == 2

        self.k_mu = float(fit.loc[lambda df: df.trait == 'Fungicide', 'mu'])
        self.k_b = float(fit.loc[lambda df: df.trait == 'Fungicide', 'b'])

        self.l_mu = float(fit.loc[lambda df: df.trait == 'Mariboss', 'mu'])
        self.l_b = float(fit.loc[lambda df: df.trait == 'Mariboss', 'b'])

        #
        #
        # SCENARIO

        if type is None:
            type_ = 'single'
        else:
            type_ = type

        # self.I0_single = DEFAULT_I0
        self.I0s = DEFAULT_I0 * np.ones(self.n_years)

        if type_ == 'single':
            self.betas = DEFAULT_BETA * np.ones(self.n_years)

        elif type_ == 'multi':
            self.beta_multi = ALL_BETAS
            self.n_iterations = n_iterations

        if verbose:
            print_string_repr(self)

    #
    #

    def remove_host_attrs(self):
        """Use if host is off and using:
        -SimulatorAsymptote
        -SimulatorSimple
        -SimulatorSimpleWithDD
        """
        remove_host_attrs_from_config(self)

    #
    #

    def print_repr(self):
        print_string_repr(self)
        #
        #
        #
        #
        #
        #


def print_string_repr(obj):
    str_out = "CONFIG\n------\n"

    for key, item in sorted(vars(obj).items()):

        this_key = (
            f"{str(key)}={str(item)}"
            .replace('{', '')
            .replace('}', '')
            # .replace('[', '')
            # .replace(']', '')
            .replace("'", '')
            .replace(' ', ', ')
            .replace(':', '--')
            .replace('=', ' = ')
            .replace(',,', ',')
        )

        if len(this_key) >= 54:
            this_key = this_key[:50] + " ..."

        str_out += this_key + "\n"

    print(str_out)


def remove_host_attrs_from_config(obj):
    for key in [
        'n_l',
        'host_on',
        'replace_cultivars',
        'mutation_scale_host',
        'l_mu',
        'l_b',
    ]:

        delattr(obj, key)


def get_asymptote_config(**kwargs):

    if 'verbose' in kwargs:
        be_verbose = kwargs['verbose']
    else:
        be_verbose = True

    kwargs['verbose'] = False

    kwargs_for_conf = copy.copy(kwargs)

    # remove if present
    kwargs_for_conf.pop('k_mu', None)
    kwargs_for_conf.pop('k_b', None)
    kwargs_for_conf.pop('curvature', None)

    cf = Config(**kwargs_for_conf)
    cf.remove_host_attrs()

    if not (
        'k_mu' in kwargs and
        'k_b' in kwargs
    ):
        k_mu = 0.99
        k_b = 0.5

    else:
        k_mu = kwargs['k_mu']
        k_b = kwargs['k_b']

    if 'curvature' in kwargs:
        curv = kwargs['curvature']
    else:
        curv = 10

    cf.k_mu = k_mu
    cf.k_b = k_b

    cf.curvature = curv

    if be_verbose:
        cf.print_repr()

    return cf
