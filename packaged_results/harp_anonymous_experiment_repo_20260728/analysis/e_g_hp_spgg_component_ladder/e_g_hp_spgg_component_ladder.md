# E-G — HP-SPGG Analytic Component Knock-Out Ladder: Complete Results

This is the single complete E-G result record. It contains the protocol, all variant definitions, all endpoint and paired statistics, every per-seed endpoint, every episode-level aggregate, the complete 1,000-row long table, semantic checks, metadata, and source hashes. The run is zero-provider; no result is tuned or filtered by direction.

## Result disposition

- Full PACT+ regret is near zero: 0.014803811559212865 mean.
- Removing the bonus is unresolved: paired 95% CI [-0.0016425044806740417, 0.0032237688015679354].
- Removing update is resolved: paired 95% CI [0.405848180944059, 0.9150662577723234].
- Removing identity raises the mean but remains unresolved: paired 95% CI [-0.14101237983986303, 1.511507453601963].
- Identity minus no-update is unresolved: paired 95% CI [-0.7669890671501177, 0.8165697021958352].
- Removing dispatch is the largest resolved effect: paired 95% CI [5.310484214436817, 7.307294886728645].

## Protocol

- n=3; type count=4; K=20; beta=0.25; Gaussian observation scale=0.08.
- Common environment seeds: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9].
- Shared per seed: iid-uniform true type profile, product-uniform prior, calibrated analytic tensor, exact centralized oracle.
- Each variant generates its own trajectory.
- Calibration SHA-256: `d6362fd4a067e1c9cc653201acf6f28d08f0e20404aeff2ec7a64f8a8697c986`.
- Oracle: exact centralized welfare argmax, shown as the zero-regret reference rather than a sixth bar.

## Variant definitions

| variant | operational definition |
|---|---|
| full | Practical PACT+ posterior-mean centralized planner with beta=0.25 and correct updates/identity. |
| minus_bonus | Same posterior-mean planner and updates as full, with the bonus disabled. |
| minus_update | Uniform profile sample every episode; no posterior update. |
| minus_identity | Correct closed-form updates; planning attaches posterior rows through a fixed seed-derived derangement. |
| minus_dispatch | Every actor has the same public-history posterior, independently samples a profile, and independently best-responds in own utility; no shared sample or joint argmax. |

## Common environments and fixed derangements

| seed | true types (0-based) | derangement (0-based) | derangement (1-based) |
|---:|---|---|---|
| 0 | [3, 2, 2] | [1, 2, 0] | [2, 3, 1] |
| 1 | [1, 2, 3] | [2, 0, 1] | [3, 1, 2] |
| 2 | [3, 1, 0] | [1, 2, 0] | [2, 3, 1] |
| 3 | [3, 0, 0] | [2, 0, 1] | [3, 1, 2] |
| 4 | [2, 3, 3] | [1, 2, 0] | [2, 3, 1] |
| 5 | [2, 3, 0] | [2, 0, 1] | [3, 1, 2] |
| 6 | [1, 2, 2] | [1, 2, 0] | [2, 3, 1] |
| 7 | [3, 2, 2] | [2, 0, 1] | [3, 1, 2] |
| 8 | [2, 1, 0] | [1, 2, 0] | [2, 3, 1] |
| 9 | [1, 3, 3] | [2, 0, 1] | [3, 1, 2] |

## K=20 endpoint summary

| variant | mean | SEM | paired minus full | paired SEM | 95% CI | covers zero | ratio vs full |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 0.014803811559212865 | 0.006791947784878735 | 0.0 | 0.0 | [0.0, 0.0] | True | 1.0 |
| minus_bonus | 0.015594443719659812 | 0.007457581701212897 | 0.0007906321604469468 | 0.0010755824932043299 | [-0.0016425044806740417, 0.0032237688015679354] | True | 1.0534073375147033 |
| minus_update | 0.6752610309174041 | 0.11361913890079703 | 0.6604572193581912 | 0.11255143657022915 | [0.405848180944059, 0.9150662577723234] | False | 45.613998004261845 |
| minus_identity | 0.7000513484402628 | 0.36842392466042223 | 0.68524753688105 | 0.3652531001514313 | [-0.14101237983986303, 1.511507453601963] | True | 47.28858818826287 |
| minus_dispatch | 6.3236933621419436 | 0.43850572649299185 | 6.308889550582731 | 0.4413510045147234 | [5.310484214436817, 7.307294886728645] | False | 427.1665669917634 |

## Per-seed K=20 endpoints and paired differences

| variant | seed | cumulative regret | variant minus full |
|---|---:|---:|---:|
| full | 0 | 0.0 | 0.0 |
| full | 1 | 0.0 | 0.0 |
| full | 2 | 0.0 | 0.0 |
| full | 3 | 0.05121318554894394 | 0.0 |
| full | 4 | 0.03449396343616895 | 0.0 |
| full | 5 | 0.014017893031915918 | 0.0 |
| full | 6 | 0.0 | 0.0 |
| full | 7 | 0.0 | 0.0 |
| full | 8 | 0.0 | 0.0 |
| full | 9 | 0.04831307357509984 | 0.0 |
| minus_bonus | 0 | 0.0 | 0.0 |
| minus_bonus | 1 | 0.0 | 0.0 |
| minus_bonus | 2 | 0.0 | 0.0 |
| minus_bonus | 3 | 0.06145582265873273 | 0.010242637109788788 |
| minus_bonus | 4 | 0.03449396343616895 | 0.0 |
| minus_bonus | 5 | 0.011681577526596598 | -0.0023363155053193196 |
| minus_bonus | 6 | 0.0 | 0.0 |
| minus_bonus | 7 | 0.0 | 0.0 |
| minus_bonus | 8 | 0.0 | 0.0 |
| minus_bonus | 9 | 0.04831307357509984 | 0.0 |
| minus_update | 0 | 0.4140757597007716 | 0.4140757597007716 |
| minus_update | 1 | 0.8142171572806594 | 0.8142171572806594 |
| minus_update | 2 | 0.468965176859371 | 0.468965176859371 |
| minus_update | 3 | 1.244912914405223 | 1.193699728856279 |
| minus_update | 4 | 0.6615059953218632 | 0.6270120318856942 |
| minus_update | 5 | 0.11850936932722811 | 0.10449147629531219 |
| minus_update | 6 | 1.2661969601899643 | 1.2661969601899643 |
| minus_update | 7 | 0.5370851827139536 | 0.5370851827139536 |
| minus_update | 8 | 0.7164766544246319 | 0.7164766544246319 |
| minus_update | 9 | 0.5106651389503754 | 0.4623520653752755 |
| minus_identity | 0 | 0.0 | 0.0 |
| minus_identity | 1 | 0.0 | 0.0 |
| minus_identity | 2 | 0.0 | 0.0 |
| minus_identity | 3 | 2.9813224485038017 | 2.9301092629548577 |
| minus_identity | 4 | 0.45230285064649145 | 0.4178088872103225 |
| minus_identity | 5 | 0.0 | -0.014017893031915918 |
| minus_identity | 6 | 0.0 | 0.0 |
| minus_identity | 7 | 2.695246915177532 | 2.695246915177532 |
| minus_identity | 8 | 0.0 | 0.0 |
| minus_identity | 9 | 0.871641270074804 | 0.8233281964997041 |
| minus_dispatch | 0 | 8.015942580845543 | 8.015942580845543 |
| minus_dispatch | 1 | 5.464474659548149 | 5.464474659548149 |
| minus_dispatch | 2 | 4.375947768395211 | 4.375947768395211 |
| minus_dispatch | 3 | 4.263683242018609 | 4.212470056469665 |
| minus_dispatch | 4 | 6.73375237140751 | 6.699258407971341 |
| minus_dispatch | 5 | 6.893301137742883 | 6.879283244710967 |
| minus_dispatch | 6 | 8.004939206690231 | 8.004939206690231 |
| minus_dispatch | 7 | 7.713724893823635 | 7.713724893823635 |
| minus_dispatch | 8 | 6.010642289113109 | 6.010642289113109 |
| minus_dispatch | 9 | 5.76052547183456 | 5.71221239825946 |

## Identity minus no-update paired contrast

| seed | minus identity | minus update | identity minus update |
|---:|---:|---:|---:|
| 0 | 0.0 | 0.4140757597007716 | -0.4140757597007716 |
| 1 | 0.0 | 0.8142171572806594 | -0.8142171572806594 |
| 2 | 0.0 | 0.468965176859371 | -0.468965176859371 |
| 3 | 2.9813224485038017 | 1.244912914405223 | 1.7364095340985788 |
| 4 | 0.45230285064649145 | 0.6615059953218632 | -0.2092031446753717 |
| 5 | 0.0 | 0.11850936932722811 | -0.11850936932722811 |
| 6 | 0.0 | 1.2661969601899643 | -1.2661969601899643 |
| 7 | 2.695246915177532 | 0.5370851827139536 | 2.1581617324635785 |
| 8 | 0.0 | 0.7164766544246319 | -0.7164766544246319 |
| 9 | 0.871641270074804 | 0.5106651389503754 | 0.3609761311244286 |

Mean: 0.024790317522858783; SEM: 0.35001077631299493; paired Student-t 95% CI: [-0.7669890671501177, 0.8165697021958352].

## Episode-level aggregate trajectories

| variant | episode | mean cumulative regret | SEM |
|---|---:|---:|---:|
| full | 1 | 0.0070840217709249535 | 0.004332338838923354 |
| full | 2 | 0.008450560519260075 | 0.0049014727131371505 |
| full | 3 | 0.009894976451105842 | 0.005559315127050658 |
| full | 4 | 0.010484985490105925 | 0.005624065143714863 |
| full | 5 | 0.011074994529106008 | 0.0057335150332346796 |
| full | 6 | 0.011665003568106092 | 0.0058851713967048615 |
| full | 7 | 0.012255012607106175 | 0.006075874582111076 |
| full | 8 | 0.012845021646106259 | 0.006302080874058917 |
| full | 9 | 0.013435030685106342 | 0.006560118641114684 |
| full | 10 | 0.014025039724106425 | 0.006846389681029478 |
| full | 11 | 0.014102916907617068 | 0.006836974350390982 |
| full | 12 | 0.014180794091127713 | 0.006828434270220703 |
| full | 13 | 0.014258671274638358 | 0.006820772728142173 |
| full | 14 | 0.014336548458149 | 0.0068139926875976755 |
| full | 15 | 0.014414425641659645 | 0.0068080967821942924 |
| full | 16 | 0.014492302825170288 | 0.006803087310643385 |
| full | 17 | 0.014570180008680933 | 0.006798966232315977 |
| full | 18 | 0.014648057192191578 | 0.006795735163433895 |
| full | 19 | 0.01472593437570222 | 0.006793395373913841 |
| full | 20 | 0.014803811559212865 | 0.006791947784878735 |
| minus_bonus | 1 | 0.0070840217709249535 | 0.004332338838923354 |
| minus_bonus | 2 | 0.008450560519260075 | 0.0049014727131371505 |
| minus_bonus | 3 | 0.009894976451105842 | 0.005559315127050658 |
| minus_bonus | 4 | 0.010484985490105925 | 0.005624065143714863 |
| minus_bonus | 5 | 0.011074994529106008 | 0.0057335150332346796 |
| minus_bonus | 6 | 0.011665003568106092 | 0.0058851713967048615 |
| minus_bonus | 7 | 0.012255012607106175 | 0.006075874582111076 |
| minus_bonus | 8 | 0.012845021646106259 | 0.006302080874058917 |
| minus_bonus | 9 | 0.013435030685106342 | 0.006560118641114684 |
| minus_bonus | 10 | 0.014025039724106425 | 0.006846389681029478 |
| minus_bonus | 11 | 0.014615048763106509 | 0.007157507148456008 |
| minus_bonus | 12 | 0.015205057802106592 | 0.007490375646960317 |
| minus_bonus | 13 | 0.015282934985617235 | 0.007482207388817008 |
| minus_bonus | 14 | 0.01536081216912788 | 0.007474841616876078 |
| minus_bonus | 15 | 0.015438689352638525 | 0.0074682807055520125 |
| minus_bonus | 16 | 0.015516566536149167 | 0.007462526777699454 |
| minus_bonus | 17 | 0.015594443719659812 | 0.007457581701212897 |
| minus_bonus | 18 | 0.015594443719659812 | 0.007457581701212897 |
| minus_bonus | 19 | 0.015594443719659812 | 0.007457581701212897 |
| minus_bonus | 20 | 0.015594443719659812 | 0.007457581701212897 |
| minus_update | 1 | 0.04183067480082969 | 0.019473546545022064 |
| minus_update | 2 | 0.07295806681859755 | 0.026371288174802728 |
| minus_update | 3 | 0.10266172579370506 | 0.040285740076406513 |
| minus_update | 4 | 0.1314423530985023 | 0.05169839087345732 |
| minus_update | 5 | 0.15018456447337092 | 0.05139312852373976 |
| minus_update | 6 | 0.16704730565463607 | 0.0492376717913974 |
| minus_update | 7 | 0.24252390636524312 | 0.06273796810610034 |
| minus_update | 8 | 0.27933009787647917 | 0.0628500886124904 |
| minus_update | 9 | 0.3103023995195941 | 0.06820319410827243 |
| minus_update | 10 | 0.3608118039445274 | 0.07536661353667981 |
| minus_update | 11 | 0.3995989986381331 | 0.06672230244364764 |
| minus_update | 12 | 0.406683020409058 | 0.0661625740691384 |
| minus_update | 13 | 0.44463248202132755 | 0.0810665965026271 |
| minus_update | 14 | 0.4832872823471638 | 0.09468293783254533 |
| minus_update | 15 | 0.5319673659291835 | 0.08945423901612659 |
| minus_update | 16 | 0.567332196182031 | 0.0987059244264983 |
| minus_update | 17 | 0.5836496737270472 | 0.09616911033987367 |
| minus_update | 18 | 0.6411569537135788 | 0.10893054195284825 |
| minus_update | 19 | 0.6642020330380827 | 0.11480318812776412 |
| minus_update | 20 | 0.6752610309174041 | 0.11361913890079703 |
| minus_identity | 1 | 0.0070840217709249535 | 0.004332338838923354 |
| minus_identity | 2 | 0.014168043541849907 | 0.008664677677846708 |
| minus_identity | 3 | 0.03592606342015834 | 0.01964977137213747 |
| minus_identity | 4 | 0.07353847691715813 | 0.03573879248164385 |
| minus_identity | 5 | 0.11115089041415793 | 0.05522498154276697 |
| minus_identity | 6 | 0.14876330391115772 | 0.0755230124533981 |
| minus_identity | 7 | 0.18637571740815753 | 0.0961199342434103 |
| minus_identity | 8 | 0.22588922748755022 | 0.11691991369658701 |
| minus_identity | 9 | 0.265402737566943 | 0.1377850193497229 |
| minus_identity | 10 | 0.3049162476463357 | 0.1586895641626002 |
| minus_identity | 11 | 0.3444297577257284 | 0.17961977861459133 |
| minus_identity | 12 | 0.3839432678051211 | 0.20056762660888205 |
| minus_identity | 13 | 0.42345677788451386 | 0.22152810588277816 |
| minus_identity | 14 | 0.46297028796390655 | 0.24249794107791744 |
| minus_identity | 15 | 0.5024837980432992 | 0.2634748983045125 |
| minus_identity | 16 | 0.541997308122692 | 0.28445740195087843 |
| minus_identity | 17 | 0.5815108182020847 | 0.3054443089848628 |
| minus_identity | 18 | 0.6210243282814775 | 0.32643477010937944 |
| minus_identity | 19 | 0.6605378383608701 | 0.347428141145781 |
| minus_identity | 20 | 0.7000513484402628 | 0.36842392466042223 |
| minus_dispatch | 1 | 0.4085462080926955 | 0.05581709302016026 |
| minus_dispatch | 2 | 0.7453732571346396 | 0.08011314252092697 |
| minus_dispatch | 3 | 1.094133519472577 | 0.06915774278361685 |
| minus_dispatch | 4 | 1.383299906067189 | 0.08357699121606783 |
| minus_dispatch | 5 | 1.6889139006803056 | 0.08841027853974516 |
| minus_dispatch | 6 | 2.015799096242465 | 0.09572248897427521 |
| minus_dispatch | 7 | 2.3165274104359246 | 0.12697748091753638 |
| minus_dispatch | 8 | 2.6483129324443704 | 0.15367845087250845 |
| minus_dispatch | 9 | 2.950453481261398 | 0.17116901404071647 |
| minus_dispatch | 10 | 3.2867959576047516 | 0.2036845371219708 |
| minus_dispatch | 11 | 3.6002466849229697 | 0.23231158667318388 |
| minus_dispatch | 12 | 3.8963487717175456 | 0.2518198071734123 |
| minus_dispatch | 13 | 4.189323580233673 | 0.2712317771044868 |
| minus_dispatch | 14 | 4.490986754034553 | 0.2924690480981373 |
| minus_dispatch | 15 | 4.79412147068683 | 0.316037688339786 |
| minus_dispatch | 16 | 5.11423588348457 | 0.3412158958266693 |
| minus_dispatch | 17 | 5.416797477363164 | 0.3644116448283392 |
| minus_dispatch | 18 | 5.71993219401544 | 0.38977577058846025 |
| minus_dispatch | 19 | 6.016076835301419 | 0.4125105203832774 |
| minus_dispatch | 20 | 6.3236933621419436 | 0.43850572649299185 |

## Semantic and acceptance checks

| check | result |
|---|---|
| Provider calls | 0 |
| Long-table rows | 1000 |
| Minus-update posterior remains exactly uniform | True |
| Decentralized actors receive identical public-history posterior inputs | True |
| Every identity mapping is a fixed-point-free derangement | True |
| Identity significantly worse than no-update | False |

## Complete metadata

```json
{
  "experiment": "E-G HP-SPGG analytic component knock-out ladder",
  "status": "complete",
  "provider_calls": 0,
  "kernel": "build_reward_tensor(n=3, backend='mixed', samples=3, seed=0, trap=False)",
  "calibration": "analysis/e_g_hp_spgg_component_ladder/calibration_analytic_n3.npy",
  "calibration_sha256": "d6362fd4a067e1c9cc653201acf6f28d08f0e20404aeff2ec7a64f8a8697c986",
  "n": 3,
  "type_count": 4,
  "action_values": 5,
  "action_profiles": 125,
  "K": 20,
  "beta": 0.25,
  "sigma": 0.08,
  "common_environment_seeds": [
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9
  ],
  "environment_matching": "shared iid-uniform true type profile, product-uniform prior, analytic tensor, and exact oracle; variant trajectories are independent conditional on the environment seed",
  "oracle": "exact centralized welfare argmax; zero-regret reference, not a bar",
  "variants": {
    "full": "practical PACT+ posterior-mean centralized objective with beta=0.25",
    "minus_bonus": "same posterior-mean centralized objective and update as full, uncertainty bonus disabled",
    "minus_update": "iid-uniform profile draw each episode, centralized sampled-profile objective, no update",
    "minus_identity": "correct update; planning posterior rows attached by a fixed derangement",
    "minus_dispatch": "same public-history factored posterior per actor; independent sampled profiles and own-utility best responses, with local disagreement bonus; no shared sample or centralized joint argmax"
  },
  "derangements": {
    "0": [
      1,
      2,
      0
    ],
    "1": [
      2,
      0,
      1
    ],
    "2": [
      1,
      2,
      0
    ],
    "3": [
      2,
      0,
      1
    ],
    "4": [
      1,
      2,
      0
    ],
    "5": [
      2,
      0,
      1
    ],
    "6": [
      1,
      2,
      0
    ],
    "7": [
      2,
      0,
      1
    ],
    "8": [
      1,
      2,
      0
    ],
    "9": [
      2,
      0,
      1
    ]
  },
  "decentralized_other_action_model": "uniform marginal over simultaneous actions of the other agents",
  "decentralized_global_spread_bonus": "omitted because no actor selects a joint action profile",
  "identity_minus_no_update": {
    "mean": 0.024790317522858783,
    "sem": 0.35001077631299493,
    "ci95": [
      -0.7669890671501177,
      0.8165697021958352
    ],
    "significantly_worse": false
  },
  "long_rows": 1000
}
```

## Source integrity

| source | bytes | SHA-256 |
|---|---:|---|
| analysis/e_g_hp_spgg_component_ladder/calibration_analytic_n3.npy | 15632 | d6362fd4a067e1c9cc653201acf6f28d08f0e20404aeff2ec7a64f8a8697c986 |
| analysis/e_g_hp_spgg_component_ladder/e_g_hp_spgg_component_ladder_long.csv | 31068 | 447e8e72c959f75cbd43b57748be3d654e39163df6c79bfb5be04f9858f9ffe6 |
| analysis/e_g_hp_spgg_component_ladder/e_g_hp_spgg_component_ladder_summary.csv | 924 | 27476a217d01972e8a548139768e5b04666813384ad5450453f8405271f3a0cd |
| analysis/e_g_hp_spgg_component_ladder/e_g_hp_spgg_component_ladder_metadata.json | 2520 | 69b74ce7d27ef95b2a17979033bfe1d4005f90bcd30c72c1fe1da916eb86401a |
| analysis/e_g_hp_spgg_component_ladder/e_g_hp_spgg_component_ladder.npz | 67122 | ab53575acadb471c047ece6c1356e32cdf00724a06635eea8aa762d445bb739d |
| arr_paper/figs/fig_e_g_hp_spgg_component_ladder.pdf | 21411 | 997529722164aedb7bc976658816b54d77d5fc13e728c015b8eabbb361eca960 |
| arr_paper/figs/fig_e_g_hp_spgg_component_trajectories.pdf | 21702 | 062863310a0ef5ffbcaeb9a6c4f2fc8ee8c352e0081d9642e0a41e5c5aab84b5 |
| scripts/run_e_g_hp_spgg_component_ladder.py | 25969 | 97227a2f0a7a300952d12f365f8d5a1e833203f5bf0e58af9586cf72150d4700 |
| scripts/plot_e_g_hp_spgg_component_ladder.py | 6229 | 5602ea51948d93e1c013d1a72956025ac43bfcb16d4391087681a48e88f07e3a |
| scripts/validate_e_g_hp_spgg_component_ladder.py | 13271 | 22681b46460455f9b8217a24eee4a1ee6a0fb6ac687b65fb8bdd2ce2abfa0a03 |

## Complete long table (all 1,000 rows)

| variant | seed | episode | cum_regret |
|---|---:|---:|---:|
| full | 0 | 1 | 0.0 |
| full | 0 | 2 | 0.0 |
| full | 0 | 3 | 0.0 |
| full | 0 | 4 | 0.0 |
| full | 0 | 5 | 0.0 |
| full | 0 | 6 | 0.0 |
| full | 0 | 7 | 0.0 |
| full | 0 | 8 | 0.0 |
| full | 0 | 9 | 0.0 |
| full | 0 | 10 | 0.0 |
| full | 0 | 11 | 0.0 |
| full | 0 | 12 | 0.0 |
| full | 0 | 13 | 0.0 |
| full | 0 | 14 | 0.0 |
| full | 0 | 15 | 0.0 |
| full | 0 | 16 | 0.0 |
| full | 0 | 17 | 0.0 |
| full | 0 | 18 | 0.0 |
| full | 0 | 19 | 0.0 |
| full | 0 | 20 | 0.0 |
| full | 1 | 1 | 0.0 |
| full | 1 | 2 | 0.0 |
| full | 1 | 3 | 0.0 |
| full | 1 | 4 | 0.0 |
| full | 1 | 5 | 0.0 |
| full | 1 | 6 | 0.0 |
| full | 1 | 7 | 0.0 |
| full | 1 | 8 | 0.0 |
| full | 1 | 9 | 0.0 |
| full | 1 | 10 | 0.0 |
| full | 1 | 11 | 0.0 |
| full | 1 | 12 | 0.0 |
| full | 1 | 13 | 0.0 |
| full | 1 | 14 | 0.0 |
| full | 1 | 15 | 0.0 |
| full | 1 | 16 | 0.0 |
| full | 1 | 17 | 0.0 |
| full | 1 | 18 | 0.0 |
| full | 1 | 19 | 0.0 |
| full | 1 | 20 | 0.0 |
| full | 2 | 1 | 0.0 |
| full | 2 | 2 | 0.0 |
| full | 2 | 3 | 0.0 |
| full | 2 | 4 | 0.0 |
| full | 2 | 5 | 0.0 |
| full | 2 | 6 | 0.0 |
| full | 2 | 7 | 0.0 |
| full | 2 | 8 | 0.0 |
| full | 2 | 9 | 0.0 |
| full | 2 | 10 | 0.0 |
| full | 2 | 11 | 0.0 |
| full | 2 | 12 | 0.0 |
| full | 2 | 13 | 0.0 |
| full | 2 | 14 | 0.0 |
| full | 2 | 15 | 0.0 |
| full | 2 | 16 | 0.0 |
| full | 2 | 17 | 0.0 |
| full | 2 | 18 | 0.0 |
| full | 2 | 19 | 0.0 |
| full | 2 | 20 | 0.0 |
| full | 3 | 1 | 0.005121318554894394 |
| full | 3 | 2 | 0.010242637109788788 |
| full | 3 | 3 | 0.015363955664683182 |
| full | 3 | 4 | 0.020485274219577576 |
| full | 3 | 5 | 0.02560659277447197 |
| full | 3 | 6 | 0.030727911329366364 |
| full | 3 | 7 | 0.03584922988426076 |
| full | 3 | 8 | 0.04097054843915515 |
| full | 3 | 9 | 0.046091866994049546 |
| full | 3 | 10 | 0.05121318554894394 |
| full | 3 | 11 | 0.05121318554894394 |
| full | 3 | 12 | 0.05121318554894394 |
| full | 3 | 13 | 0.05121318554894394 |
| full | 3 | 14 | 0.05121318554894394 |
| full | 3 | 15 | 0.05121318554894394 |
| full | 3 | 16 | 0.05121318554894394 |
| full | 3 | 17 | 0.05121318554894394 |
| full | 3 | 18 | 0.05121318554894394 |
| full | 3 | 19 | 0.05121318554894394 |
| full | 3 | 20 | 0.05121318554894394 |
| full | 4 | 1 | 0.03449396343616895 |
| full | 4 | 2 | 0.03449396343616895 |
| full | 4 | 3 | 0.03449396343616895 |
| full | 4 | 4 | 0.03449396343616895 |
| full | 4 | 5 | 0.03449396343616895 |
| full | 4 | 6 | 0.03449396343616895 |
| full | 4 | 7 | 0.03449396343616895 |
| full | 4 | 8 | 0.03449396343616895 |
| full | 4 | 9 | 0.03449396343616895 |
| full | 4 | 10 | 0.03449396343616895 |
| full | 4 | 11 | 0.03449396343616895 |
| full | 4 | 12 | 0.03449396343616895 |
| full | 4 | 13 | 0.03449396343616895 |
| full | 4 | 14 | 0.03449396343616895 |
| full | 4 | 15 | 0.03449396343616895 |
| full | 4 | 16 | 0.03449396343616895 |
| full | 4 | 17 | 0.03449396343616895 |
| full | 4 | 18 | 0.03449396343616895 |
| full | 4 | 19 | 0.03449396343616895 |
| full | 4 | 20 | 0.03449396343616895 |
| full | 5 | 1 | 0.0 |
| full | 5 | 2 | 0.0 |
| full | 5 | 3 | 0.0007787718351064399 |
| full | 5 | 4 | 0.0015575436702128798 |
| full | 5 | 5 | 0.0023363155053193196 |
| full | 5 | 6 | 0.0031150873404257595 |
| full | 5 | 7 | 0.0038938591755321994 |
| full | 5 | 8 | 0.004672631010638639 |
| full | 5 | 9 | 0.005451402845745079 |
| full | 5 | 10 | 0.006230174680851519 |
| full | 5 | 11 | 0.007008946515957959 |
| full | 5 | 12 | 0.007787718351064399 |
| full | 5 | 13 | 0.008566490186170839 |
| full | 5 | 14 | 0.009345262021277279 |
| full | 5 | 15 | 0.010124033856383718 |
| full | 5 | 16 | 0.010902805691490158 |
| full | 5 | 17 | 0.011681577526596598 |
| full | 5 | 18 | 0.012460349361703038 |
| full | 5 | 19 | 0.013239121196809478 |
| full | 5 | 20 | 0.014017893031915918 |
| full | 6 | 1 | 0.0 |
| full | 6 | 2 | 0.0 |
| full | 6 | 3 | 0.0 |
| full | 6 | 4 | 0.0 |
| full | 6 | 5 | 0.0 |
| full | 6 | 6 | 0.0 |
| full | 6 | 7 | 0.0 |
| full | 6 | 8 | 0.0 |
| full | 6 | 9 | 0.0 |
| full | 6 | 10 | 0.0 |
| full | 6 | 11 | 0.0 |
| full | 6 | 12 | 0.0 |
| full | 6 | 13 | 0.0 |
| full | 6 | 14 | 0.0 |
| full | 6 | 15 | 0.0 |
| full | 6 | 16 | 0.0 |
| full | 6 | 17 | 0.0 |
| full | 6 | 18 | 0.0 |
| full | 6 | 19 | 0.0 |
| full | 6 | 20 | 0.0 |
| full | 7 | 1 | 0.0 |
| full | 7 | 2 | 0.0 |
| full | 7 | 3 | 0.0 |
| full | 7 | 4 | 0.0 |
| full | 7 | 5 | 0.0 |
| full | 7 | 6 | 0.0 |
| full | 7 | 7 | 0.0 |
| full | 7 | 8 | 0.0 |
| full | 7 | 9 | 0.0 |
| full | 7 | 10 | 0.0 |
| full | 7 | 11 | 0.0 |
| full | 7 | 12 | 0.0 |
| full | 7 | 13 | 0.0 |
| full | 7 | 14 | 0.0 |
| full | 7 | 15 | 0.0 |
| full | 7 | 16 | 0.0 |
| full | 7 | 17 | 0.0 |
| full | 7 | 18 | 0.0 |
| full | 7 | 19 | 0.0 |
| full | 7 | 20 | 0.0 |
| full | 8 | 1 | 0.0 |
| full | 8 | 2 | 0.0 |
| full | 8 | 3 | 0.0 |
| full | 8 | 4 | 0.0 |
| full | 8 | 5 | 0.0 |
| full | 8 | 6 | 0.0 |
| full | 8 | 7 | 0.0 |
| full | 8 | 8 | 0.0 |
| full | 8 | 9 | 0.0 |
| full | 8 | 10 | 0.0 |
| full | 8 | 11 | 0.0 |
| full | 8 | 12 | 0.0 |
| full | 8 | 13 | 0.0 |
| full | 8 | 14 | 0.0 |
| full | 8 | 15 | 0.0 |
| full | 8 | 16 | 0.0 |
| full | 8 | 17 | 0.0 |
| full | 8 | 18 | 0.0 |
| full | 8 | 19 | 0.0 |
| full | 8 | 20 | 0.0 |
| full | 9 | 1 | 0.031224935718186186 |
| full | 9 | 2 | 0.039769004646643014 |
| full | 9 | 3 | 0.04831307357509984 |
| full | 9 | 4 | 0.04831307357509984 |
| full | 9 | 5 | 0.04831307357509984 |
| full | 9 | 6 | 0.04831307357509984 |
| full | 9 | 7 | 0.04831307357509984 |
| full | 9 | 8 | 0.04831307357509984 |
| full | 9 | 9 | 0.04831307357509984 |
| full | 9 | 10 | 0.04831307357509984 |
| full | 9 | 11 | 0.04831307357509984 |
| full | 9 | 12 | 0.04831307357509984 |
| full | 9 | 13 | 0.04831307357509984 |
| full | 9 | 14 | 0.04831307357509984 |
| full | 9 | 15 | 0.04831307357509984 |
| full | 9 | 16 | 0.04831307357509984 |
| full | 9 | 17 | 0.04831307357509984 |
| full | 9 | 18 | 0.04831307357509984 |
| full | 9 | 19 | 0.04831307357509984 |
| full | 9 | 20 | 0.04831307357509984 |
| minus_bonus | 0 | 1 | 0.0 |
| minus_bonus | 0 | 2 | 0.0 |
| minus_bonus | 0 | 3 | 0.0 |
| minus_bonus | 0 | 4 | 0.0 |
| minus_bonus | 0 | 5 | 0.0 |
| minus_bonus | 0 | 6 | 0.0 |
| minus_bonus | 0 | 7 | 0.0 |
| minus_bonus | 0 | 8 | 0.0 |
| minus_bonus | 0 | 9 | 0.0 |
| minus_bonus | 0 | 10 | 0.0 |
| minus_bonus | 0 | 11 | 0.0 |
| minus_bonus | 0 | 12 | 0.0 |
| minus_bonus | 0 | 13 | 0.0 |
| minus_bonus | 0 | 14 | 0.0 |
| minus_bonus | 0 | 15 | 0.0 |
| minus_bonus | 0 | 16 | 0.0 |
| minus_bonus | 0 | 17 | 0.0 |
| minus_bonus | 0 | 18 | 0.0 |
| minus_bonus | 0 | 19 | 0.0 |
| minus_bonus | 0 | 20 | 0.0 |
| minus_bonus | 1 | 1 | 0.0 |
| minus_bonus | 1 | 2 | 0.0 |
| minus_bonus | 1 | 3 | 0.0 |
| minus_bonus | 1 | 4 | 0.0 |
| minus_bonus | 1 | 5 | 0.0 |
| minus_bonus | 1 | 6 | 0.0 |
| minus_bonus | 1 | 7 | 0.0 |
| minus_bonus | 1 | 8 | 0.0 |
| minus_bonus | 1 | 9 | 0.0 |
| minus_bonus | 1 | 10 | 0.0 |
| minus_bonus | 1 | 11 | 0.0 |
| minus_bonus | 1 | 12 | 0.0 |
| minus_bonus | 1 | 13 | 0.0 |
| minus_bonus | 1 | 14 | 0.0 |
| minus_bonus | 1 | 15 | 0.0 |
| minus_bonus | 1 | 16 | 0.0 |
| minus_bonus | 1 | 17 | 0.0 |
| minus_bonus | 1 | 18 | 0.0 |
| minus_bonus | 1 | 19 | 0.0 |
| minus_bonus | 1 | 20 | 0.0 |
| minus_bonus | 2 | 1 | 0.0 |
| minus_bonus | 2 | 2 | 0.0 |
| minus_bonus | 2 | 3 | 0.0 |
| minus_bonus | 2 | 4 | 0.0 |
| minus_bonus | 2 | 5 | 0.0 |
| minus_bonus | 2 | 6 | 0.0 |
| minus_bonus | 2 | 7 | 0.0 |
| minus_bonus | 2 | 8 | 0.0 |
| minus_bonus | 2 | 9 | 0.0 |
| minus_bonus | 2 | 10 | 0.0 |
| minus_bonus | 2 | 11 | 0.0 |
| minus_bonus | 2 | 12 | 0.0 |
| minus_bonus | 2 | 13 | 0.0 |
| minus_bonus | 2 | 14 | 0.0 |
| minus_bonus | 2 | 15 | 0.0 |
| minus_bonus | 2 | 16 | 0.0 |
| minus_bonus | 2 | 17 | 0.0 |
| minus_bonus | 2 | 18 | 0.0 |
| minus_bonus | 2 | 19 | 0.0 |
| minus_bonus | 2 | 20 | 0.0 |
| minus_bonus | 3 | 1 | 0.005121318554894394 |
| minus_bonus | 3 | 2 | 0.010242637109788788 |
| minus_bonus | 3 | 3 | 0.015363955664683182 |
| minus_bonus | 3 | 4 | 0.020485274219577576 |
| minus_bonus | 3 | 5 | 0.02560659277447197 |
| minus_bonus | 3 | 6 | 0.030727911329366364 |
| minus_bonus | 3 | 7 | 0.03584922988426076 |
| minus_bonus | 3 | 8 | 0.04097054843915515 |
| minus_bonus | 3 | 9 | 0.046091866994049546 |
| minus_bonus | 3 | 10 | 0.05121318554894394 |
| minus_bonus | 3 | 11 | 0.056334504103838334 |
| minus_bonus | 3 | 12 | 0.06145582265873273 |
| minus_bonus | 3 | 13 | 0.06145582265873273 |
| minus_bonus | 3 | 14 | 0.06145582265873273 |
| minus_bonus | 3 | 15 | 0.06145582265873273 |
| minus_bonus | 3 | 16 | 0.06145582265873273 |
| minus_bonus | 3 | 17 | 0.06145582265873273 |
| minus_bonus | 3 | 18 | 0.06145582265873273 |
| minus_bonus | 3 | 19 | 0.06145582265873273 |
| minus_bonus | 3 | 20 | 0.06145582265873273 |
| minus_bonus | 4 | 1 | 0.03449396343616895 |
| minus_bonus | 4 | 2 | 0.03449396343616895 |
| minus_bonus | 4 | 3 | 0.03449396343616895 |
| minus_bonus | 4 | 4 | 0.03449396343616895 |
| minus_bonus | 4 | 5 | 0.03449396343616895 |
| minus_bonus | 4 | 6 | 0.03449396343616895 |
| minus_bonus | 4 | 7 | 0.03449396343616895 |
| minus_bonus | 4 | 8 | 0.03449396343616895 |
| minus_bonus | 4 | 9 | 0.03449396343616895 |
| minus_bonus | 4 | 10 | 0.03449396343616895 |
| minus_bonus | 4 | 11 | 0.03449396343616895 |
| minus_bonus | 4 | 12 | 0.03449396343616895 |
| minus_bonus | 4 | 13 | 0.03449396343616895 |
| minus_bonus | 4 | 14 | 0.03449396343616895 |
| minus_bonus | 4 | 15 | 0.03449396343616895 |
| minus_bonus | 4 | 16 | 0.03449396343616895 |
| minus_bonus | 4 | 17 | 0.03449396343616895 |
| minus_bonus | 4 | 18 | 0.03449396343616895 |
| minus_bonus | 4 | 19 | 0.03449396343616895 |
| minus_bonus | 4 | 20 | 0.03449396343616895 |
| minus_bonus | 5 | 1 | 0.0 |
| minus_bonus | 5 | 2 | 0.0 |
| minus_bonus | 5 | 3 | 0.0007787718351064399 |
| minus_bonus | 5 | 4 | 0.0015575436702128798 |
| minus_bonus | 5 | 5 | 0.0023363155053193196 |
| minus_bonus | 5 | 6 | 0.0031150873404257595 |
| minus_bonus | 5 | 7 | 0.0038938591755321994 |
| minus_bonus | 5 | 8 | 0.004672631010638639 |
| minus_bonus | 5 | 9 | 0.005451402845745079 |
| minus_bonus | 5 | 10 | 0.006230174680851519 |
| minus_bonus | 5 | 11 | 0.007008946515957959 |
| minus_bonus | 5 | 12 | 0.007787718351064399 |
| minus_bonus | 5 | 13 | 0.008566490186170839 |
| minus_bonus | 5 | 14 | 0.009345262021277279 |
| minus_bonus | 5 | 15 | 0.010124033856383718 |
| minus_bonus | 5 | 16 | 0.010902805691490158 |
| minus_bonus | 5 | 17 | 0.011681577526596598 |
| minus_bonus | 5 | 18 | 0.011681577526596598 |
| minus_bonus | 5 | 19 | 0.011681577526596598 |
| minus_bonus | 5 | 20 | 0.011681577526596598 |
| minus_bonus | 6 | 1 | 0.0 |
| minus_bonus | 6 | 2 | 0.0 |
| minus_bonus | 6 | 3 | 0.0 |
| minus_bonus | 6 | 4 | 0.0 |
| minus_bonus | 6 | 5 | 0.0 |
| minus_bonus | 6 | 6 | 0.0 |
| minus_bonus | 6 | 7 | 0.0 |
| minus_bonus | 6 | 8 | 0.0 |
| minus_bonus | 6 | 9 | 0.0 |
| minus_bonus | 6 | 10 | 0.0 |
| minus_bonus | 6 | 11 | 0.0 |
| minus_bonus | 6 | 12 | 0.0 |
| minus_bonus | 6 | 13 | 0.0 |
| minus_bonus | 6 | 14 | 0.0 |
| minus_bonus | 6 | 15 | 0.0 |
| minus_bonus | 6 | 16 | 0.0 |
| minus_bonus | 6 | 17 | 0.0 |
| minus_bonus | 6 | 18 | 0.0 |
| minus_bonus | 6 | 19 | 0.0 |
| minus_bonus | 6 | 20 | 0.0 |
| minus_bonus | 7 | 1 | 0.0 |
| minus_bonus | 7 | 2 | 0.0 |
| minus_bonus | 7 | 3 | 0.0 |
| minus_bonus | 7 | 4 | 0.0 |
| minus_bonus | 7 | 5 | 0.0 |
| minus_bonus | 7 | 6 | 0.0 |
| minus_bonus | 7 | 7 | 0.0 |
| minus_bonus | 7 | 8 | 0.0 |
| minus_bonus | 7 | 9 | 0.0 |
| minus_bonus | 7 | 10 | 0.0 |
| minus_bonus | 7 | 11 | 0.0 |
| minus_bonus | 7 | 12 | 0.0 |
| minus_bonus | 7 | 13 | 0.0 |
| minus_bonus | 7 | 14 | 0.0 |
| minus_bonus | 7 | 15 | 0.0 |
| minus_bonus | 7 | 16 | 0.0 |
| minus_bonus | 7 | 17 | 0.0 |
| minus_bonus | 7 | 18 | 0.0 |
| minus_bonus | 7 | 19 | 0.0 |
| minus_bonus | 7 | 20 | 0.0 |
| minus_bonus | 8 | 1 | 0.0 |
| minus_bonus | 8 | 2 | 0.0 |
| minus_bonus | 8 | 3 | 0.0 |
| minus_bonus | 8 | 4 | 0.0 |
| minus_bonus | 8 | 5 | 0.0 |
| minus_bonus | 8 | 6 | 0.0 |
| minus_bonus | 8 | 7 | 0.0 |
| minus_bonus | 8 | 8 | 0.0 |
| minus_bonus | 8 | 9 | 0.0 |
| minus_bonus | 8 | 10 | 0.0 |
| minus_bonus | 8 | 11 | 0.0 |
| minus_bonus | 8 | 12 | 0.0 |
| minus_bonus | 8 | 13 | 0.0 |
| minus_bonus | 8 | 14 | 0.0 |
| minus_bonus | 8 | 15 | 0.0 |
| minus_bonus | 8 | 16 | 0.0 |
| minus_bonus | 8 | 17 | 0.0 |
| minus_bonus | 8 | 18 | 0.0 |
| minus_bonus | 8 | 19 | 0.0 |
| minus_bonus | 8 | 20 | 0.0 |
| minus_bonus | 9 | 1 | 0.031224935718186186 |
| minus_bonus | 9 | 2 | 0.039769004646643014 |
| minus_bonus | 9 | 3 | 0.04831307357509984 |
| minus_bonus | 9 | 4 | 0.04831307357509984 |
| minus_bonus | 9 | 5 | 0.04831307357509984 |
| minus_bonus | 9 | 6 | 0.04831307357509984 |
| minus_bonus | 9 | 7 | 0.04831307357509984 |
| minus_bonus | 9 | 8 | 0.04831307357509984 |
| minus_bonus | 9 | 9 | 0.04831307357509984 |
| minus_bonus | 9 | 10 | 0.04831307357509984 |
| minus_bonus | 9 | 11 | 0.04831307357509984 |
| minus_bonus | 9 | 12 | 0.04831307357509984 |
| minus_bonus | 9 | 13 | 0.04831307357509984 |
| minus_bonus | 9 | 14 | 0.04831307357509984 |
| minus_bonus | 9 | 15 | 0.04831307357509984 |
| minus_bonus | 9 | 16 | 0.04831307357509984 |
| minus_bonus | 9 | 17 | 0.04831307357509984 |
| minus_bonus | 9 | 18 | 0.04831307357509984 |
| minus_bonus | 9 | 19 | 0.04831307357509984 |
| minus_bonus | 9 | 20 | 0.04831307357509984 |
| minus_update | 0 | 1 | 0.0 |
| minus_update | 0 | 2 | 0.0 |
| minus_update | 0 | 3 | 0.0 |
| minus_update | 0 | 4 | 0.0 |
| minus_update | 0 | 5 | 0.0 |
| minus_update | 0 | 6 | 0.09700842226829565 |
| minus_update | 0 | 7 | 0.09700842226829565 |
| minus_update | 0 | 8 | 0.2555523584552093 |
| minus_update | 0 | 9 | 0.2555523584552093 |
| minus_update | 0 | 10 | 0.31706733743247595 |
| minus_update | 0 | 11 | 0.31706733743247595 |
| minus_update | 0 | 12 | 0.31706733743247595 |
| minus_update | 0 | 13 | 0.31706733743247595 |
| minus_update | 0 | 14 | 0.31706733743247595 |
| minus_update | 0 | 15 | 0.31706733743247595 |
| minus_update | 0 | 16 | 0.31706733743247595 |
| minus_update | 0 | 17 | 0.31706733743247595 |
| minus_update | 0 | 18 | 0.4140757597007716 |
| minus_update | 0 | 19 | 0.4140757597007716 |
| minus_update | 0 | 20 | 0.4140757597007716 |
| minus_update | 1 | 1 | 0.11731252118880642 |
| minus_update | 1 | 2 | 0.2561258831048172 |
| minus_update | 1 | 3 | 0.4030521341004958 |
| minus_update | 1 | 4 | 0.5499783850961744 |
| minus_update | 1 | 5 | 0.5499783850961744 |
| minus_update | 1 | 6 | 0.5499783850961744 |
| minus_update | 1 | 7 | 0.6969046360918529 |
| minus_update | 1 | 8 | 0.6969046360918529 |
| minus_update | 1 | 9 | 0.8142171572806594 |
| minus_update | 1 | 10 | 0.8142171572806594 |
| minus_update | 1 | 11 | 0.8142171572806594 |
| minus_update | 1 | 12 | 0.8142171572806594 |
| minus_update | 1 | 13 | 0.8142171572806594 |
| minus_update | 1 | 14 | 0.8142171572806594 |
| minus_update | 1 | 15 | 0.8142171572806594 |
| minus_update | 1 | 16 | 0.8142171572806594 |
| minus_update | 1 | 17 | 0.8142171572806594 |
| minus_update | 1 | 18 | 0.8142171572806594 |
| minus_update | 1 | 19 | 0.8142171572806594 |
| minus_update | 1 | 20 | 0.8142171572806594 |
| minus_update | 2 | 1 | 0.0 |
| minus_update | 2 | 2 | 0.0 |
| minus_update | 2 | 3 | 0.0 |
| minus_update | 2 | 4 | 0.039749761083963886 |
| minus_update | 2 | 5 | 0.039749761083963886 |
| minus_update | 2 | 6 | 0.039749761083963886 |
| minus_update | 2 | 7 | 0.039749761083963886 |
| minus_update | 2 | 8 | 0.039749761083963886 |
| minus_update | 2 | 9 | 0.08898358654935423 |
| minus_update | 2 | 10 | 0.08898358654935423 |
| minus_update | 2 | 11 | 0.3402318292260529 |
| minus_update | 2 | 12 | 0.3402318292260529 |
| minus_update | 2 | 13 | 0.3402318292260529 |
| minus_update | 2 | 14 | 0.3402318292260529 |
| minus_update | 2 | 15 | 0.38946565469144323 |
| minus_update | 2 | 16 | 0.38946565469144323 |
| minus_update | 2 | 17 | 0.4292154157754071 |
| minus_update | 2 | 18 | 0.4292154157754071 |
| minus_update | 2 | 19 | 0.4292154157754071 |
| minus_update | 2 | 20 | 0.468965176859371 |
| minus_update | 3 | 1 | 0.005121318554894394 |
| minus_update | 3 | 2 | 0.010242637109788788 |
| minus_update | 3 | 3 | 0.015363955664683182 |
| minus_update | 3 | 4 | 0.020485274219577576 |
| minus_update | 3 | 5 | 0.02560659277447197 |
| minus_update | 3 | 6 | 0.030727911329366364 |
| minus_update | 3 | 7 | 0.36718449508743545 |
| minus_update | 3 | 8 | 0.37230581364232984 |
| minus_update | 3 | 9 | 0.37742713219722424 |
| minus_update | 3 | 10 | 0.5424871217191138 |
| minus_update | 3 | 11 | 0.5476084402740082 |
| minus_update | 3 | 12 | 0.5527297588289026 |
| minus_update | 3 | 13 | 0.8891863425869717 |
| minus_update | 3 | 14 | 1.0542463321088613 |
| minus_update | 3 | 15 | 1.0593676506637557 |
| minus_update | 3 | 16 | 1.06448896921865 |
| minus_update | 3 | 17 | 1.0696102877735445 |
| minus_update | 3 | 18 | 1.234670277295434 |
| minus_update | 3 | 19 | 1.2397915958503285 |
| minus_update | 3 | 20 | 1.244912914405223 |
| minus_update | 4 | 1 | 0.0 |
| minus_update | 4 | 2 | 0.0745993250113206 |
| minus_update | 4 | 3 | 0.10909328844748956 |
| minus_update | 4 | 4 | 0.1435872518836585 |
| minus_update | 4 | 5 | 0.17808121531982746 |
| minus_update | 4 | 6 | 0.2125751787559964 |
| minus_update | 4 | 7 | 0.287174503767317 |
| minus_update | 4 | 8 | 0.32166846720348596 |
| minus_update | 4 | 9 | 0.32166846720348596 |
| minus_update | 4 | 10 | 0.3561624306396549 |
| minus_update | 4 | 11 | 0.39065639407582387 |
| minus_update | 4 | 12 | 0.4251503575119928 |
| minus_update | 4 | 13 | 0.45964432094816177 |
| minus_update | 4 | 14 | 0.4809395944911703 |
| minus_update | 4 | 15 | 0.5154335579273392 |
| minus_update | 4 | 16 | 0.5499275213635082 |
| minus_update | 4 | 17 | 0.5712227949065167 |
| minus_update | 4 | 18 | 0.5925180684495253 |
| minus_update | 4 | 19 | 0.6270120318856942 |
| minus_update | 4 | 20 | 0.6615059953218632 |
| minus_update | 5 | 1 | 0.0 |
| minus_update | 5 | 2 | 0.0 |
| minus_update | 5 | 3 | 0.0 |
| minus_update | 5 | 4 | 0.0 |
| minus_update | 5 | 5 | 0.0 |
| minus_update | 5 | 6 | 0.0007787718351064399 |
| minus_update | 5 | 7 | 0.0007787718351064399 |
| minus_update | 5 | 8 | 0.0007787718351064399 |
| minus_update | 5 | 9 | 0.039011110393149195 |
| minus_update | 5 | 10 | 0.07949825893407891 |
| minus_update | 5 | 11 | 0.07949825893407891 |
| minus_update | 5 | 12 | 0.07949825893407891 |
| minus_update | 5 | 13 | 0.07949825893407891 |
| minus_update | 5 | 14 | 0.07949825893407891 |
| minus_update | 5 | 15 | 0.11773059749212167 |
| minus_update | 5 | 16 | 0.11773059749212167 |
| minus_update | 5 | 17 | 0.11773059749212167 |
| minus_update | 5 | 18 | 0.11850936932722811 |
| minus_update | 5 | 19 | 0.11850936932722811 |
| minus_update | 5 | 20 | 0.11850936932722811 |
| minus_update | 6 | 1 | 0.16269698471053373 |
| minus_update | 6 | 2 | 0.16269698471053373 |
| minus_update | 6 | 3 | 0.16269698471053373 |
| minus_update | 6 | 4 | 0.16269698471053373 |
| minus_update | 6 | 5 | 0.16269698471053373 |
| minus_update | 6 | 6 | 0.16269698471053373 |
| minus_update | 6 | 7 | 0.29088275510570716 |
| minus_update | 6 | 8 | 0.4295605163219043 |
| minus_update | 6 | 9 | 0.4295605163219043 |
| minus_update | 6 | 10 | 0.6330984800949822 |
| minus_update | 6 | 11 | 0.6330984800949822 |
| minus_update | 6 | 12 | 0.6330984800949822 |
| minus_update | 6 | 13 | 0.6330984800949822 |
| minus_update | 6 | 14 | 0.7717762413111793 |
| minus_update | 6 | 15 | 0.7717762413111793 |
| minus_update | 6 | 16 | 0.9753142050842571 |
| minus_update | 6 | 17 | 0.9753142050842571 |
| minus_update | 6 | 18 | 1.1380111897947909 |
| minus_update | 6 | 19 | 1.2661969601899643 |
| minus_update | 6 | 20 | 1.2661969601899643 |
| minus_update | 7 | 1 | 0.0 |
| minus_update | 7 | 2 | 0.061514978977266654 |
| minus_update | 7 | 3 | 0.061514978977266654 |
| minus_update | 7 | 4 | 0.12302995795453331 |
| minus_update | 7 | 5 | 0.18454493693179996 |
| minus_update | 7 | 6 | 0.18454493693179996 |
| minus_update | 7 | 7 | 0.18454493693179996 |
| minus_update | 7 | 8 | 0.18454493693179996 |
| minus_update | 7 | 9 | 0.18454493693179996 |
| minus_update | 7 | 10 | 0.18454493693179996 |
| minus_update | 7 | 11 | 0.2815533592000956 |
| minus_update | 7 | 12 | 0.2815533592000956 |
| minus_update | 7 | 13 | 0.2815533592000956 |
| minus_update | 7 | 14 | 0.34306833817736226 |
| minus_update | 7 | 15 | 0.34306833817736226 |
| minus_update | 7 | 16 | 0.34306833817736226 |
| minus_update | 7 | 17 | 0.4400767604456579 |
| minus_update | 7 | 18 | 0.5370851827139536 |
| minus_update | 7 | 19 | 0.5370851827139536 |
| minus_update | 7 | 20 | 0.5370851827139536 |
| minus_update | 8 | 1 | 0.1019509878358762 |
| minus_update | 8 | 2 | 0.1019509878358762 |
| minus_update | 8 | 3 | 0.2039019756717524 |
| minus_update | 8 | 4 | 0.2039019756717524 |
| minus_update | 8 | 5 | 0.2039019756717524 |
| minus_update | 8 | 6 | 0.2039019756717524 |
| minus_update | 8 | 7 | 0.27250005261758137 |
| minus_update | 8 | 8 | 0.27250005261758137 |
| minus_update | 8 | 9 | 0.34109812956341035 |
| minus_update | 8 | 10 | 0.34109812956341035 |
| minus_update | 8 | 11 | 0.34109812956341035 |
| minus_update | 8 | 12 | 0.34109812956341035 |
| minus_update | 8 | 13 | 0.34109812956341035 |
| minus_update | 8 | 14 | 0.34109812956341035 |
| minus_update | 8 | 15 | 0.6145256665887557 |
| minus_update | 8 | 16 | 0.7164766544246319 |
| minus_update | 8 | 17 | 0.7164766544246319 |
| minus_update | 8 | 18 | 0.7164766544246319 |
| minus_update | 8 | 19 | 0.7164766544246319 |
| minus_update | 8 | 20 | 0.7164766544246319 |
| minus_update | 9 | 1 | 0.031224935718186186 |
| minus_update | 9 | 2 | 0.06244987143637237 |
| minus_update | 9 | 3 | 0.0709939403648292 |
| minus_update | 9 | 4 | 0.0709939403648292 |
| minus_update | 9 | 5 | 0.15728579314518543 |
| minus_update | 9 | 6 | 0.1885107288633716 |
| minus_update | 9 | 7 | 0.1885107288633716 |
| minus_update | 9 | 8 | 0.2197356645815578 |
| minus_update | 9 | 9 | 0.250960600299744 |
| minus_update | 9 | 10 | 0.250960600299744 |
| minus_update | 9 | 11 | 0.250960600299744 |
| minus_update | 9 | 12 | 0.28218553601793017 |
| minus_update | 9 | 13 | 0.290729604946387 |
| minus_update | 9 | 14 | 0.290729604946387 |
| minus_update | 9 | 15 | 0.3770214577267432 |
| minus_update | 9 | 16 | 0.38556552665520005 |
| minus_update | 9 | 17 | 0.38556552665520005 |
| minus_update | 9 | 18 | 0.41679046237338624 |
| minus_update | 9 | 19 | 0.47944020323218917 |
| minus_update | 9 | 20 | 0.5106651389503754 |
| minus_identity | 0 | 1 | 0.0 |
| minus_identity | 0 | 2 | 0.0 |
| minus_identity | 0 | 3 | 0.0 |
| minus_identity | 0 | 4 | 0.0 |
| minus_identity | 0 | 5 | 0.0 |
| minus_identity | 0 | 6 | 0.0 |
| minus_identity | 0 | 7 | 0.0 |
| minus_identity | 0 | 8 | 0.0 |
| minus_identity | 0 | 9 | 0.0 |
| minus_identity | 0 | 10 | 0.0 |
| minus_identity | 0 | 11 | 0.0 |
| minus_identity | 0 | 12 | 0.0 |
| minus_identity | 0 | 13 | 0.0 |
| minus_identity | 0 | 14 | 0.0 |
| minus_identity | 0 | 15 | 0.0 |
| minus_identity | 0 | 16 | 0.0 |
| minus_identity | 0 | 17 | 0.0 |
| minus_identity | 0 | 18 | 0.0 |
| minus_identity | 0 | 19 | 0.0 |
| minus_identity | 0 | 20 | 0.0 |
| minus_identity | 1 | 1 | 0.0 |
| minus_identity | 1 | 2 | 0.0 |
| minus_identity | 1 | 3 | 0.0 |
| minus_identity | 1 | 4 | 0.0 |
| minus_identity | 1 | 5 | 0.0 |
| minus_identity | 1 | 6 | 0.0 |
| minus_identity | 1 | 7 | 0.0 |
| minus_identity | 1 | 8 | 0.0 |
| minus_identity | 1 | 9 | 0.0 |
| minus_identity | 1 | 10 | 0.0 |
| minus_identity | 1 | 11 | 0.0 |
| minus_identity | 1 | 12 | 0.0 |
| minus_identity | 1 | 13 | 0.0 |
| minus_identity | 1 | 14 | 0.0 |
| minus_identity | 1 | 15 | 0.0 |
| minus_identity | 1 | 16 | 0.0 |
| minus_identity | 1 | 17 | 0.0 |
| minus_identity | 1 | 18 | 0.0 |
| minus_identity | 1 | 19 | 0.0 |
| minus_identity | 1 | 20 | 0.0 |
| minus_identity | 2 | 1 | 0.0 |
| minus_identity | 2 | 2 | 0.0 |
| minus_identity | 2 | 3 | 0.0 |
| minus_identity | 2 | 4 | 0.0 |
| minus_identity | 2 | 5 | 0.0 |
| minus_identity | 2 | 6 | 0.0 |
| minus_identity | 2 | 7 | 0.0 |
| minus_identity | 2 | 8 | 0.0 |
| minus_identity | 2 | 9 | 0.0 |
| minus_identity | 2 | 10 | 0.0 |
| minus_identity | 2 | 11 | 0.0 |
| minus_identity | 2 | 12 | 0.0 |
| minus_identity | 2 | 13 | 0.0 |
| minus_identity | 2 | 14 | 0.0 |
| minus_identity | 2 | 15 | 0.0 |
| minus_identity | 2 | 16 | 0.0 |
| minus_identity | 2 | 17 | 0.0 |
| minus_identity | 2 | 18 | 0.0 |
| minus_identity | 2 | 19 | 0.0 |
| minus_identity | 2 | 20 | 0.0 |
| minus_identity | 3 | 1 | 0.005121318554894394 |
| minus_identity | 3 | 2 | 0.010242637109788788 |
| minus_identity | 3 | 3 | 0.1753026266316784 |
| minus_identity | 3 | 4 | 0.340362616153568 |
| minus_identity | 3 | 5 | 0.5054226056754576 |
| minus_identity | 3 | 6 | 0.6704825951973472 |
| minus_identity | 3 | 7 | 0.8355425847192368 |
| minus_identity | 3 | 8 | 1.0006025742411264 |
| minus_identity | 3 | 9 | 1.165662563763016 |
| minus_identity | 3 | 10 | 1.3307225532849056 |
| minus_identity | 3 | 11 | 1.4957825428067952 |
| minus_identity | 3 | 12 | 1.6608425323286848 |
| minus_identity | 3 | 13 | 1.8259025218505744 |
| minus_identity | 3 | 14 | 1.990962511372464 |
| minus_identity | 3 | 15 | 2.1560225008943537 |
| minus_identity | 3 | 16 | 2.3210824904162433 |
| minus_identity | 3 | 17 | 2.486142479938133 |
| minus_identity | 3 | 18 | 2.6512024694600225 |
| minus_identity | 3 | 19 | 2.816262458981912 |
| minus_identity | 3 | 20 | 2.9813224485038017 |
| minus_identity | 4 | 1 | 0.03449396343616895 |
| minus_identity | 4 | 2 | 0.0689879268723379 |
| minus_identity | 4 | 3 | 0.09028320041534643 |
| minus_identity | 4 | 4 | 0.11157847395835496 |
| minus_identity | 4 | 5 | 0.1328737475013635 |
| minus_identity | 4 | 6 | 0.15416902104437202 |
| minus_identity | 4 | 7 | 0.17546429458738055 |
| minus_identity | 4 | 8 | 0.19675956813038908 |
| minus_identity | 4 | 9 | 0.21805484167339761 |
| minus_identity | 4 | 10 | 0.23935011521640615 |
| minus_identity | 4 | 11 | 0.2606453887594147 |
| minus_identity | 4 | 12 | 0.2819406623024232 |
| minus_identity | 4 | 13 | 0.30323593584543174 |
| minus_identity | 4 | 14 | 0.32453120938844027 |
| minus_identity | 4 | 15 | 0.3458264829314488 |
| minus_identity | 4 | 16 | 0.36712175647445733 |
| minus_identity | 4 | 17 | 0.38841703001746586 |
| minus_identity | 4 | 18 | 0.4097123035604744 |
| minus_identity | 4 | 19 | 0.4310075771034829 |
| minus_identity | 4 | 20 | 0.45230285064649145 |
| minus_identity | 5 | 1 | 0.0 |
| minus_identity | 5 | 2 | 0.0 |
| minus_identity | 5 | 3 | 0.0 |
| minus_identity | 5 | 4 | 0.0 |
| minus_identity | 5 | 5 | 0.0 |
| minus_identity | 5 | 6 | 0.0 |
| minus_identity | 5 | 7 | 0.0 |
| minus_identity | 5 | 8 | 0.0 |
| minus_identity | 5 | 9 | 0.0 |
| minus_identity | 5 | 10 | 0.0 |
| minus_identity | 5 | 11 | 0.0 |
| minus_identity | 5 | 12 | 0.0 |
| minus_identity | 5 | 13 | 0.0 |
| minus_identity | 5 | 14 | 0.0 |
| minus_identity | 5 | 15 | 0.0 |
| minus_identity | 5 | 16 | 0.0 |
| minus_identity | 5 | 17 | 0.0 |
| minus_identity | 5 | 18 | 0.0 |
| minus_identity | 5 | 19 | 0.0 |
| minus_identity | 5 | 20 | 0.0 |
| minus_identity | 6 | 1 | 0.0 |
| minus_identity | 6 | 2 | 0.0 |
| minus_identity | 6 | 3 | 0.0 |
| minus_identity | 6 | 4 | 0.0 |
| minus_identity | 6 | 5 | 0.0 |
| minus_identity | 6 | 6 | 0.0 |
| minus_identity | 6 | 7 | 0.0 |
| minus_identity | 6 | 8 | 0.0 |
| minus_identity | 6 | 9 | 0.0 |
| minus_identity | 6 | 10 | 0.0 |
| minus_identity | 6 | 11 | 0.0 |
| minus_identity | 6 | 12 | 0.0 |
| minus_identity | 6 | 13 | 0.0 |
| minus_identity | 6 | 14 | 0.0 |
| minus_identity | 6 | 15 | 0.0 |
| minus_identity | 6 | 16 | 0.0 |
| minus_identity | 6 | 17 | 0.0 |
| minus_identity | 6 | 18 | 0.0 |
| minus_identity | 6 | 19 | 0.0 |
| minus_identity | 6 | 20 | 0.0 |
| minus_identity | 7 | 1 | 0.0 |
| minus_identity | 7 | 2 | 0.0 |
| minus_identity | 7 | 3 | 0.0 |
| minus_identity | 7 | 4 | 0.15854393618691365 |
| minus_identity | 7 | 5 | 0.3170878723738273 |
| minus_identity | 7 | 6 | 0.47563180856074094 |
| minus_identity | 7 | 7 | 0.6341757447476546 |
| minus_identity | 7 | 8 | 0.7927196809345682 |
| minus_identity | 7 | 9 | 0.9512636171214819 |
| minus_identity | 7 | 10 | 1.1098075533083955 |
| minus_identity | 7 | 11 | 1.2683514894953092 |
| minus_identity | 7 | 12 | 1.4268954256822228 |
| minus_identity | 7 | 13 | 1.5854393618691365 |
| minus_identity | 7 | 14 | 1.7439832980560501 |
| minus_identity | 7 | 15 | 1.9025272342429638 |
| minus_identity | 7 | 16 | 2.0610711704298774 |
| minus_identity | 7 | 17 | 2.219615106616791 |
| minus_identity | 7 | 18 | 2.3781590428037047 |
| minus_identity | 7 | 19 | 2.5367029789906184 |
| minus_identity | 7 | 20 | 2.695246915177532 |
| minus_identity | 8 | 1 | 0.0 |
| minus_identity | 8 | 2 | 0.0 |
| minus_identity | 8 | 3 | 0.0 |
| minus_identity | 8 | 4 | 0.0 |
| minus_identity | 8 | 5 | 0.0 |
| minus_identity | 8 | 6 | 0.0 |
| minus_identity | 8 | 7 | 0.0 |
| minus_identity | 8 | 8 | 0.0 |
| minus_identity | 8 | 9 | 0.0 |
| minus_identity | 8 | 10 | 0.0 |
| minus_identity | 8 | 11 | 0.0 |
| minus_identity | 8 | 12 | 0.0 |
| minus_identity | 8 | 13 | 0.0 |
| minus_identity | 8 | 14 | 0.0 |
| minus_identity | 8 | 15 | 0.0 |
| minus_identity | 8 | 16 | 0.0 |
| minus_identity | 8 | 17 | 0.0 |
| minus_identity | 8 | 18 | 0.0 |
| minus_identity | 8 | 19 | 0.0 |
| minus_identity | 8 | 20 | 0.0 |
| minus_identity | 9 | 1 | 0.031224935718186186 |
| minus_identity | 9 | 2 | 0.06244987143637237 |
| minus_identity | 9 | 3 | 0.09367480715455856 |
| minus_identity | 9 | 4 | 0.12489974287274475 |
| minus_identity | 9 | 5 | 0.15612467859093093 |
| minus_identity | 9 | 6 | 0.18734961430911712 |
| minus_identity | 9 | 7 | 0.2185745500273033 |
| minus_identity | 9 | 8 | 0.26881045156941874 |
| minus_identity | 9 | 9 | 0.3190463531115342 |
| minus_identity | 9 | 10 | 0.3692822546536496 |
| minus_identity | 9 | 11 | 0.41951815619576505 |
| minus_identity | 9 | 12 | 0.4697540577378805 |
| minus_identity | 9 | 13 | 0.5199899592799959 |
| minus_identity | 9 | 14 | 0.5702258608221114 |
| minus_identity | 9 | 15 | 0.6204617623642268 |
| minus_identity | 9 | 16 | 0.6706976639063422 |
| minus_identity | 9 | 17 | 0.7209335654484577 |
| minus_identity | 9 | 18 | 0.7711694669905731 |
| minus_identity | 9 | 19 | 0.8214053685326885 |
| minus_identity | 9 | 20 | 0.871641270074804 |
| minus_dispatch | 0 | 1 | 0.40825492195373747 |
| minus_dispatch | 0 | 2 | 0.6549531976763168 |
| minus_dispatch | 0 | 3 | 0.985408024223863 |
| minus_dispatch | 0 | 4 | 1.4427618118591872 |
| minus_dispatch | 0 | 5 | 1.8302148458315517 |
| minus_dispatch | 0 | 6 | 2.2176678798039164 |
| minus_dispatch | 0 | 7 | 2.6051209137762807 |
| minus_dispatch | 0 | 8 | 3.0324314523545057 |
| minus_dispatch | 0 | 9 | 3.4798435616373498 |
| minus_dispatch | 0 | 10 | 3.998649865910318 |
| minus_dispatch | 0 | 11 | 4.3291046924578644 |
| minus_dispatch | 0 | 12 | 4.716557726430229 |
| minus_dispatch | 0 | 13 | 5.104010760402593 |
| minus_dispatch | 0 | 14 | 5.491463794374957 |
| minus_dispatch | 0 | 15 | 5.878916828347322 |
| minus_dispatch | 0 | 16 | 6.336270615982646 |
| minus_dispatch | 0 | 17 | 6.72372364995501 |
| minus_dispatch | 0 | 18 | 7.181077437590335 |
| minus_dispatch | 0 | 19 | 7.568530471562699 |
| minus_dispatch | 0 | 20 | 8.015942580845543 |
| minus_dispatch | 1 | 1 | 0.448041659742034 |
| minus_dispatch | 1 | 2 | 0.6666121845621085 |
| minus_dispatch | 1 | 3 | 1.0545116032412192 |
| minus_dispatch | 1 | 4 | 1.30158775482232 |
| minus_dispatch | 1 | 5 | 1.5486639064034209 |
| minus_dispatch | 1 | 6 | 1.7957400579845217 |
| minus_dispatch | 1 | 7 | 2.042816209565623 |
| minus_dispatch | 1 | 8 | 2.4995608405749365 |
| minus_dispatch | 1 | 9 | 2.7466369921560374 |
| minus_dispatch | 1 | 10 | 2.9937131437371383 |
| minus_dispatch | 1 | 11 | 3.240789295318239 |
| minus_dispatch | 1 | 12 | 3.48786544689934 |
| minus_dispatch | 1 | 13 | 3.734941598480441 |
| minus_dispatch | 1 | 14 | 3.9820177500615417 |
| minus_dispatch | 1 | 15 | 4.229093901642642 |
| minus_dispatch | 1 | 16 | 4.476170053223743 |
| minus_dispatch | 1 | 17 | 4.723246204804845 |
| minus_dispatch | 1 | 18 | 4.970322356385946 |
| minus_dispatch | 1 | 19 | 5.217398507967047 |
| minus_dispatch | 1 | 20 | 5.464474659548149 |
| minus_dispatch | 2 | 1 | 0.6483578238773773 |
| minus_dispatch | 2 | 2 | 0.8893744185764167 |
| minus_dispatch | 2 | 3 | 1.0765239097985886 |
| minus_dispatch | 2 | 4 | 1.232501291074325 |
| minus_dispatch | 2 | 5 | 1.4196507822964968 |
| minus_dispatch | 2 | 6 | 1.710718463728074 |
| minus_dispatch | 2 | 7 | 1.8978679549502457 |
| minus_dispatch | 2 | 8 | 2.085017446172418 |
| minus_dispatch | 2 | 9 | 2.27216693739459 |
| minus_dispatch | 2 | 10 | 2.459316428616762 |
| minus_dispatch | 2 | 11 | 2.646465919838934 |
| minus_dispatch | 2 | 12 | 2.833615411061106 |
| minus_dispatch | 2 | 13 | 3.020764902283278 |
| minus_dispatch | 2 | 14 | 3.20791439350545 |
| minus_dispatch | 2 | 15 | 3.395063884727622 |
| minus_dispatch | 2 | 16 | 3.6273498035065224 |
| minus_dispatch | 2 | 17 | 3.8144992947286944 |
| minus_dispatch | 2 | 18 | 4.0016487859508665 |
| minus_dispatch | 2 | 19 | 4.1887982771730385 |
| minus_dispatch | 2 | 20 | 4.375947768395211 |
| minus_dispatch | 3 | 1 | 0.40133136141690406 |
| minus_dispatch | 3 | 2 | 1.1078265847525968 |
| minus_dispatch | 3 | 3 | 1.2581066685932618 |
| minus_dispatch | 3 | 4 | 1.5541084677154515 |
| minus_dispatch | 3 | 5 | 1.8000660022850636 |
| minus_dispatch | 3 | 6 | 1.9584702669396303 |
| minus_dispatch | 3 | 7 | 2.2044278015092424 |
| minus_dispatch | 3 | 8 | 2.362832066163809 |
| minus_dispatch | 3 | 9 | 2.521236330818376 |
| minus_dispatch | 3 | 10 | 2.6796405954729425 |
| minus_dispatch | 3 | 11 | 2.8380448601275092 |
| minus_dispatch | 3 | 12 | 2.996449124782076 |
| minus_dispatch | 3 | 13 | 3.1548533894366426 |
| minus_dispatch | 3 | 14 | 3.3132576540912093 |
| minus_dispatch | 3 | 15 | 3.471661918745776 |
| minus_dispatch | 3 | 16 | 3.6300661834003427 |
| minus_dispatch | 3 | 17 | 3.7884704480549094 |
| minus_dispatch | 3 | 18 | 3.946874712709476 |
| minus_dispatch | 3 | 19 | 4.105278977364042 |
| minus_dispatch | 3 | 20 | 4.263683242018609 |
| minus_dispatch | 4 | 1 | 0.3688214855866625 |
| minus_dispatch | 4 | 2 | 0.6642372263619756 |
| minus_dispatch | 4 | 3 | 1.033058711948638 |
| minus_dispatch | 4 | 4 | 1.346694872386286 |
| minus_dispatch | 4 | 5 | 1.642110613161599 |
| minus_dispatch | 4 | 6 | 2.066919499535365 |
| minus_dispatch | 4 | 7 | 2.380555659973013 |
| minus_dispatch | 4 | 8 | 2.7493771455596754 |
| minus_dispatch | 4 | 9 | 3.0630133059973232 |
| minus_dispatch | 4 | 10 | 3.376649466434971 |
| minus_dispatch | 4 | 11 | 3.690285626872619 |
| minus_dispatch | 4 | 12 | 4.003921787310267 |
| minus_dispatch | 4 | 13 | 4.317557947747915 |
| minus_dispatch | 4 | 14 | 4.686379433334578 |
| minus_dispatch | 4 | 15 | 5.0000155937722255 |
| minus_dispatch | 4 | 16 | 5.368837079358888 |
| minus_dispatch | 4 | 17 | 5.737658564945551 |
| minus_dispatch | 4 | 18 | 6.051294725383199 |
| minus_dispatch | 4 | 19 | 6.364930885820847 |
| minus_dispatch | 4 | 20 | 6.73375237140751 |
| minus_dispatch | 5 | 1 | 0.7006946966965961 |
| minus_dispatch | 5 | 2 | 0.8840705336530659 |
| minus_dispatch | 5 | 3 | 1.3050086551187654 |
| minus_dispatch | 5 | 4 | 1.4523981465757245 |
| minus_dispatch | 5 | 5 | 1.781021641425149 |
| minus_dispatch | 5 | 6 | 2.2019597628908487 |
| minus_dispatch | 5 | 7 | 2.530583257740273 |
| minus_dispatch | 5 | 8 | 2.8592067525896976 |
| minus_dispatch | 5 | 9 | 3.187830247439122 |
| minus_dispatch | 5 | 10 | 3.6087683689048218 |
| minus_dispatch | 5 | 11 | 3.936966318840201 |
| minus_dispatch | 5 | 12 | 4.26516426877558 |
| minus_dispatch | 5 | 13 | 4.593787763625004 |
| minus_dispatch | 5 | 14 | 4.922411258474428 |
| minus_dispatch | 5 | 15 | 5.251034753323852 |
| minus_dispatch | 5 | 16 | 5.5792327032592315 |
| minus_dispatch | 5 | 17 | 5.9078561981086555 |
| minus_dispatch | 5 | 18 | 6.2364796929580795 |
| minus_dispatch | 5 | 19 | 6.5651031878075035 |
| minus_dispatch | 5 | 20 | 6.893301137742883 |
| minus_dispatch | 6 | 1 | 0.2715244587866017 |
| minus_dispatch | 6 | 2 | 1.005642236082499 |
| minus_dispatch | 6 | 3 | 1.5040568979630389 |
| minus_dispatch | 6 | 4 | 2.0024715598435785 |
| minus_dispatch | 6 | 5 | 2.3485562383154597 |
| minus_dispatch | 6 | 6 | 2.685656716010219 |
| minus_dispatch | 6 | 7 | 3.1833410527032653 |
| minus_dispatch | 6 | 8 | 3.6817557145838054 |
| minus_dispatch | 6 | 9 | 4.018856192278565 |
| minus_dispatch | 6 | 10 | 4.464366369967227 |
| minus_dispatch | 6 | 11 | 4.962050706660273 |
| minus_dispatch | 6 | 12 | 5.299151184355033 |
| minus_dispatch | 6 | 13 | 5.636251662049792 |
| minus_dispatch | 6 | 14 | 5.973352139744552 |
| minus_dispatch | 6 | 15 | 6.310452617439312 |
| minus_dispatch | 6 | 16 | 6.6475530951340716 |
| minus_dispatch | 6 | 17 | 6.993637773605952 |
| minus_dispatch | 6 | 18 | 7.330738251300712 |
| minus_dispatch | 6 | 19 | 7.667838728995472 |
| minus_dispatch | 6 | 20 | 8.004939206690231 |
| minus_dispatch | 7 | 1 | 0.24620384566425924 |
| minus_dispatch | 7 | 2 | 0.694749713842508 |
| minus_dispatch | 7 | 3 | 1.0358117233720272 |
| minus_dispatch | 7 | 4 | 1.2665716633124828 |
| minus_dispatch | 7 | 5 | 1.6540246972848474 |
| minus_dispatch | 7 | 6 | 2.0414777312572117 |
| minus_dispatch | 7 | 7 | 2.428930765229576 |
| minus_dispatch | 7 | 8 | 2.8163837992019403 |
| minus_dispatch | 7 | 9 | 3.2038368331743046 |
| minus_dispatch | 7 | 10 | 3.661190620809629 |
| minus_dispatch | 7 | 11 | 4.118544408444953 |
| minus_dispatch | 7 | 12 | 4.505997442417318 |
| minus_dispatch | 7 | 13 | 4.861752148691164 |
| minus_dispatch | 7 | 14 | 5.249205182663529 |
| minus_dispatch | 7 | 15 | 5.706558970298853 |
| minus_dispatch | 7 | 16 | 6.1639127579341775 |
| minus_dispatch | 7 | 17 | 6.551365791906542 |
| minus_dispatch | 7 | 18 | 6.938818825878906 |
| minus_dispatch | 7 | 19 | 7.32627185985127 |
| minus_dispatch | 7 | 20 | 7.713724893823635 |
| minus_dispatch | 8 | 1 | 0.11731752108733673 |
| minus_dispatch | 8 | 2 | 0.1859155980331657 |
| minus_dispatch | 8 | 3 | 0.6935657391110968 |
| minus_dispatch | 8 | 4 | 1.0131836600369661 |
| minus_dispatch | 8 | 5 | 1.4186738750635997 |
| minus_dispatch | 8 | 6 | 1.738291795989469 |
| minus_dispatch | 8 | 7 | 1.8556093170768058 |
| minus_dispatch | 8 | 8 | 2.175227238002675 |
| minus_dispatch | 8 | 9 | 2.4948451589285443 |
| minus_dispatch | 8 | 10 | 2.8144630798544137 |
| minus_dispatch | 8 | 11 | 3.134081000780283 |
| minus_dispatch | 8 | 12 | 3.4536989217061524 |
| minus_dispatch | 8 | 13 | 3.773316842632022 |
| minus_dispatch | 8 | 14 | 4.092934763557891 |
| minus_dispatch | 8 | 15 | 4.41255268448376 |
| minus_dispatch | 8 | 16 | 4.73217060540963 |
| minus_dispatch | 8 | 17 | 5.0517885263355 |
| minus_dispatch | 8 | 18 | 5.37140644726137 |
| minus_dispatch | 8 | 19 | 5.6910243681872394 |
| minus_dispatch | 8 | 20 | 6.010642289113109 |
| minus_dispatch | 9 | 1 | 0.47491430611544516 |
| minus_dispatch | 9 | 2 | 0.7003508778057438 |
| minus_dispatch | 9 | 3 | 0.9952832613552703 |
| minus_dispatch | 9 | 4 | 1.2207198330455689 |
| minus_dispatch | 9 | 5 | 1.4461564047358675 |
| minus_dispatch | 9 | 6 | 1.741088788285394 |
| minus_dispatch | 9 | 7 | 2.0360211718349204 |
| minus_dispatch | 9 | 8 | 2.2213368692402415 |
| minus_dispatch | 9 | 9 | 2.516269252789768 |
| minus_dispatch | 9 | 10 | 2.8112016363392947 |
| minus_dispatch | 9 | 11 | 3.106134019888821 |
| minus_dispatch | 9 | 12 | 3.4010664034383478 |
| minus_dispatch | 9 | 13 | 3.6959987869878743 |
| minus_dispatch | 9 | 14 | 3.990931170537401 |
| minus_dispatch | 9 | 15 | 4.285863554086927 |
| minus_dispatch | 9 | 16 | 4.580795937636454 |
| minus_dispatch | 9 | 17 | 4.8757283211859805 |
| minus_dispatch | 9 | 18 | 5.170660704735507 |
| minus_dispatch | 9 | 19 | 5.465593088285034 |
| minus_dispatch | 9 | 20 | 5.76052547183456 |

## Coverage checks

- Environment rows: 10.
- Endpoint summary rows: 5.
- Per-seed endpoint rows: 50.
- Identity-vs-no-update paired rows: 10.
- Episode aggregate rows: 100.
- Complete long rows: 1000.
- Source-integrity rows: 10.
