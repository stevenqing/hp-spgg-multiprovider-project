# Claim B v2 — Theory-Aligned Stochastic-Channel Pilot

This is a new pilot, not a replacement or retuning of the completed preregistered scaling run. It targets the per-agent posterior contraction used in Proposition `prop:tid-collapse`.

## Design

- Outcomes are sampled from the Gaussian channel used by the likelihood: `y ~ Normal(mu_true, sigma^2)`.
- A fixed all-contribution HP-SPGG action isolates the outcome channel and gives a measured action-specific Hellinger margin.
- Type/horizon phase: n=3, m in {4,8,16}, H in {1,4,16}.
- Population phase: m=8, H=4, n in {2,4,8,16}.
- 200 seeds, posterior threshold 0.9, maximum 2,000 turns; censored observations are retained.
- Per-agent predictor: log(m*sqrt(m))/(rho_action*H), matching the proof switching term up to constants.
- All-agent predictor: [log(m*sqrt(m))+log(n)]/(rho_action*H), using log(n), not linear n.

## Cell summaries

| phase | n | m | H | rho action | per-agent predictor | all-agent predictor | median per-agent | median all-agent | censored agents | censored seeds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| type_horizon | 3 | 4 | 1 | 0.07433819726669055 | 27.972719518873664 | 42.75129001240883 | 6.0 | 9.0 | 0 | 0 |
| type_horizon | 3 | 4 | 4 | 0.07433819726669055 | 6.993179879718416 | 10.687822503102208 | 2.0 | 3.0 | 0 | 0 |
| type_horizon | 3 | 4 | 16 | 0.07433819726669055 | 1.748294969929604 | 2.671955625775552 | 1.0 | 1.0 | 0 | 0 |
| type_horizon | 3 | 8 | 1 | 0.015992267610175137 | 195.04190328425818 | 263.7383705675541 | 52.0 | 74.0 | 0 | 0 |
| type_horizon | 3 | 8 | 4 | 0.015992267610175137 | 48.760475821064546 | 65.93459264188853 | 13.0 | 19.0 | 0 | 0 |
| type_horizon | 3 | 8 | 16 | 0.015992267610175137 | 12.190118955266136 | 16.483648160472132 | 4.0 | 5.0 | 0 | 0 |
| type_horizon | 3 | 16 | 1 | 0.0035047535997874135 | 1186.6406481790718 | 1500.1041363782845 | 243.0 | 358.0 | 0 | 0 |
| type_horizon | 3 | 16 | 4 | 0.0035047535997874135 | 296.66016204476796 | 375.0260340945711 | 61.0 | 90.0 | 0 | 0 |
| type_horizon | 3 | 16 | 16 | 0.0035047535997874135 | 74.16504051119199 | 93.75650852364278 | 16.0 | 23.0 | 0 | 0 |
| population | 2 | 8 | 4 | 0.015992267610175137 | 48.760475821064546 | 59.596137114634445 | 13.0 | 17.0 | 0 | 0 |
| population | 4 | 8 | 4 | 0.015992267610175137 | 48.760475821064546 | 70.43179840820434 | 14.0 | 23.0 | 0 | 0 |
| population | 8 | 8 | 4 | 0.015992267610175137 | 48.760475821064546 | 81.26745970177424 | 14.0 | 28.0 | 0 | 0 |
| population | 16 | 8 | 4 | 0.015992267610175137 | 48.760475821064546 | 92.10312099534414 | 13.0 | 35.5 | 0 | 0 |

## Pilot fits

```json
{
  "status": "pilot",
  "provider_calls": 0,
  "stochastic_channel": "y ~ Normal(mu_true(action), sigma^2)",
  "diagnostic_action": "all agents contribute 1.0",
  "seeds": [
    2000,
    2001,
    2002,
    2003,
    2004,
    2005,
    2006,
    2007,
    2008,
    2009,
    2010,
    2011,
    2012,
    2013,
    2014,
    2015,
    2016,
    2017,
    2018,
    2019,
    2020,
    2021,
    2022,
    2023,
    2024,
    2025,
    2026,
    2027,
    2028,
    2029,
    2030,
    2031,
    2032,
    2033,
    2034,
    2035,
    2036,
    2037,
    2038,
    2039,
    2040,
    2041,
    2042,
    2043,
    2044,
    2045,
    2046,
    2047,
    2048,
    2049,
    2050,
    2051,
    2052,
    2053,
    2054,
    2055,
    2056,
    2057,
    2058,
    2059,
    2060,
    2061,
    2062,
    2063,
    2064,
    2065,
    2066,
    2067,
    2068,
    2069,
    2070,
    2071,
    2072,
    2073,
    2074,
    2075,
    2076,
    2077,
    2078,
    2079,
    2080,
    2081,
    2082,
    2083,
    2084,
    2085,
    2086,
    2087,
    2088,
    2089,
    2090,
    2091,
    2092,
    2093,
    2094,
    2095,
    2096,
    2097,
    2098,
    2099,
    2100,
    2101,
    2102,
    2103,
    2104,
    2105,
    2106,
    2107,
    2108,
    2109,
    2110,
    2111,
    2112,
    2113,
    2114,
    2115,
    2116,
    2117,
    2118,
    2119,
    2120,
    2121,
    2122,
    2123,
    2124,
    2125,
    2126,
    2127,
    2128,
    2129,
    2130,
    2131,
    2132,
    2133,
    2134,
    2135,
    2136,
    2137,
    2138,
    2139,
    2140,
    2141,
    2142,
    2143,
    2144,
    2145,
    2146,
    2147,
    2148,
    2149,
    2150,
    2151,
    2152,
    2153,
    2154,
    2155,
    2156,
    2157,
    2158,
    2159,
    2160,
    2161,
    2162,
    2163,
    2164,
    2165,
    2166,
    2167,
    2168,
    2169,
    2170,
    2171,
    2172,
    2173,
    2174,
    2175,
    2176,
    2177,
    2178,
    2179,
    2180,
    2181,
    2182,
    2183,
    2184,
    2185,
    2186,
    2187,
    2188,
    2189,
    2190,
    2191,
    2192,
    2193,
    2194,
    2195,
    2196,
    2197,
    2198,
    2199
  ],
  "max_turns": 2000,
  "threshold": 0.9,
  "type_horizon_fit": {
    "slope": 0.20369048984087515,
    "intercept": 2.3486053769731337,
    "r_squared": 0.9975948564535484,
    "observations": 9
  },
  "population_fit": {
    "slope": 0.5583415572052063,
    "intercept": -16.47499999999997,
    "r_squared": 0.9936206311503223,
    "observations": 4
  },
  "limitations": [
    "H points reuse one stochastic turn stream and are regrouped into episodes; they are not independent cells.",
    "Only three unique type-library sizes and four population sizes are included.",
    "The diagnostic action is fixed rather than selected by the adaptive PACT planner.",
    "OLS is on cell medians; a full study should fit seed/agent first-passage data with bootstrap or survival methods.",
    "The action-specific rho is not the proposition's worst-case uniform rho over every reachable action."
  ]
}
```

## Interpretation rule

The pilot is promising only if the type/horizon fit has a positive slope and materially nonzero R-squared, H approximately rescales first-passage episodes inversely, and the population fit is compatible with log(n). Censored cells remain censored; they are not deleted or imputed into OLS.

## Pilot limitations

The high R-squared values are evidence that the corrected variables are aligned, not final theorem validation. H points reuse the same stochastic turn streams and differ by episode grouping; only three m values and four n values are available; the action is fixed; and OLS treats cell medians rather than seed/agent first-passage observations. A confirmatory run should use independent cell replicates or a hierarchical/survival model and should separately test the adaptive planner with realized information accumulation.
