# Structural Surrogates for All-Cause Mortality Estimation Without Outcome Data: A Verifiable Autoresearch Framework

## Abstract
Estimating all-cause mortality (ACM) from a small set of physiological variables is ordinarily impossible without mortality-linked cohorts, life tables, age, or externally calibrated hazard ratios. This constraint becomes acute when the available variables are arbitrary, sparse, or selected specifically to avoid overlap with known epidemiologic datasets. We propose a reframing: instead of directly estimating ACM, one should search for an explicit structural surrogate of mortality risk whose form is constrained by verifiable criteria rather than fitted outcome data.

The central methodological contribution is a framework for autoresearch over formula space in which candidate ACM-like functions are optimized against a battery of monotonicity, dominance, smoothness, boundedness, and invariance tests. This replaces unverifiable constants with explicit structural assumptions and converts the problem from supervised risk prediction to constrained scientific search. We argue that the most suitable latent target is not biological age, chronological-age-adjusted hazard, or disease-specific risk, but a universal proxy such as physiologic reserve, homeostatic dysregulation, or multi-system slack. We derive three candidate estimator families using only VO2max, visceral fat, HbA1c, and ApoB, then show why these should not be ensembled ad hoc, but instead treated as competing mechanistic hypotheses to be compared under a formal verification harness. The resulting framework is suitable for LLM-guided scientific exploration under severe data scarcity and is designed to be auditable, falsifiable, and extensible.

## 1. Introduction
The usual route from biomarkers to all-cause mortality is straightforward in principle: assemble a cohort, collect predictors, observe deaths, and fit a survival model. In practice, this route fails under several conditions: age is unavailable or disallowed, external mortality-linked cohorts do not exist for the chosen variables, direct access to cases and controls is impossible, and literature-derived hazard ratios are too heterogeneous or weakly transportable to support credible synthesis.

Under these constraints, asking for a calibrated ACM estimate is ill-posed. Any explicit mortality formula would ordinarily require hidden constants derived from external data. If such constants cannot be estimated, then direct ACM prediction collapses into arbitrary numerology. The key insight is that this does not prevent progress altogether. It merely changes the object of interest.

Instead of fitting mortality, one can search for a formula that behaves like a mortality surrogate should behave. This shifts the problem from one of empirical calibration to one of structural validity. The central question becomes: what mathematical properties must any credible ACM-like function satisfy, independent of outcome data? Once those properties are made explicit and testable, an automated research loop can search over candidate formulas and retain only those that satisfy the criteria.

This is especially attractive for LLM-based autoresearch systems. Such systems are strongest when they can iteratively propose, evaluate, and refine hypotheses under a clear reward signal. If the reward is direct predictive accuracy, mortality data are needed. If the reward is structural coherence under verifiable constraints, the loop can operate without mortality labels. The result is not true ACM, but a formulaic surrogate suitable for later calibration.

## 2. Problem Formulation
Let the available inputs be:

- `v`: VO2max
- `f`: visceral fat
- `h`: HbA1c
- `a`: ApoB

The goal is to construct a scalar function

$$
R(v,f,h,a)
$$

intended to behave like annual all-cause mortality risk or, more cautiously, like a monotone surrogate thereof.

The classical formulation would require estimating

$$
P(\text{death within one year} \mid v,f,h,a)
$$

from data. We explicitly reject this formulation under the stated constraints. Instead, we seek a function $R$ satisfying:

- directional plausibility: worse physiology should not lower risk,
- dominance consistency: a profile that is better on every dimension should have lower risk,
- smoothness: small input changes should not cause unstable output jumps,
- boundedness: risk should stay in a plausible range,
- interpretability: the formula should remain explicit and auditable,
- searchability: the space of candidate formulas should be navigable by an autoresearch system.

The outcome is therefore a structurally validated ACM-like estimator, not a calibrated mortality model.

## 3. Why Direct ACM Estimation Fails
Direct ACM estimation is blocked by identifiability. With only a few physiological inputs and no mortality-linked external anchor, many incompatible risk mappings are equally consistent with the observed variables. Without age, the problem is even less constrained, because the same biomarker pattern can correspond to radically different absolute mortality in different age strata. If cases and controls are unavailable and literature effect sizes are prohibited, there is no empirical mechanism for assigning quantitative hazard ratios.

This means that a direct ACM formula of the form

$$
R(v,f,h,a) = \text{some explicit equation}
$$

cannot be called mortality unless its constants come from somewhere real. If not, the constants are merely encoded preference. The methodological breakthrough proposed here is not to deny this limitation, but to work around it by changing what the constants mean. They are no longer claimed to be mortality coefficients; they become parameters in a structural hypothesis, selected by passing a rigorous verification suite.

## 4. Candidate Latent Targets
The first key design choice is the latent construct. Among many possibilities, three emerged as especially strong.

### 4.1 Physiologic Reserve
Physiologic reserve is the margin between current function and systemic failure. Higher VO2max suggests greater reserve; elevated visceral fat, HbA1c, and ApoB imply cumulative metabolic and vascular burden that may erode that reserve. Mortality is presumed to rise as reserve shrinks.

This target is attractive because it is general, not disease-specific, and can absorb arbitrary future variables.

### 4.2 Homeostatic Dysregulation
Homeostatic dysregulation treats risk as a function of multivariate distance from an internally coherent robust state. It does not ask whether a single marker is bad, but whether the full vector reflects a physiologically strained or incoherent configuration. This view naturally supports distance-based formulas.

### 4.3 Multi-System Slack
Slack is the minimal margin across subsystems. Under this framing, the body behaves like a system limited by its weakest bottleneck. If VO2max, visceral fat, HbA1c, and ApoB are each mapped to a normalized reserve margin, then total vulnerability may be approximated by the smallest of those margins.

These three latent targets are preferred because they are universal, compatible with arbitrary variable sets, and expressible without invoking age or disease-specific endpoints.

## 5. Three Explicit Estimator Families
To illustrate the framework, we define explicit candidate annual ACM-like estimators from the four inputs alone. These are not validated mortality models; they are structural hypotheses.

Define one-sided standardized deficits:

$$
d_v = \max\left( \frac{35-v}{10}, 0 \right)
$$

$$
d_f = \max\left( \frac{f-80}{40}, 0 \right)
$$

$$
d_h = \max\left( \frac{h-5.4}{0.5}, 0 \right)
$$

$$
d_a = \max\left( \frac{a-80}{30}, 0 \right)
$$

These encode worsening from a nominal reference state.

### 5.1 Reserve-Burden Multiplicative Estimator
The first candidate expresses risk as multiplicative accumulation of burden with a simple interaction between visceral fat and HbA1c:

$$
HR_1 =
1.6^{d_v}
\cdot
1.4^{d_f}
\cdot
1.5^{d_h}
\cdot
1.3^{d_a}
\cdot
1.15^{d_f d_h}
$$

and

$$
R_1(v,f,h,a) = 100 \cdot \min\left(0.20,\; 0.002 \cdot HR_1\right)
$$

This formula assumes that low fitness, adiposity, dysglycemia, and atherogenic lipoprotein burden each increase risk monotonically, while visceral fat and glycemia interact synergistically.

### 5.2 Dysregulation-Distance Estimator
The second candidate treats total risk as an increasing nonlinear function of multivariate deviation from a robust reference state:

$$
M = \sqrt{d_v^2 + d_f^2 + d_h^2 + d_a^2}
$$

$$
R_2(v,f,h,a) = 100 \cdot \min\left(0.20,\; 0.002 \cdot e^{0.8M + 0.3M^2}\right)
$$

This formula captures the intuition that isolated mild abnormalities should matter less than coordinated multi-domain deviation.

### 5.3 Weakest-Link Slack Estimator
The third candidate maps each variable to a normalized margin:

$$
s_v = \frac{v}{35}, \quad
s_f = \frac{80}{f}, \quad
s_h = \frac{5.4}{h}, \quad
s_a = \frac{80}{a}
$$

Then define

$$
W = \min(s_v,s_f,s_h,s_a)
$$

and

$$
R_3(v,f,h,a) = 100 \cdot \min\left(0.20,\; \frac{0.002}{W^2}\right)
$$

This formula embodies a bottleneck model: total risk is set by the weakest physiological subsystem.

## 6. Why These Estimators Should Not Be Arbitrarily Combined
A tempting move is to ensemble several candidate estimators, for example by taking their median. That is methodologically weak unless there is a formal reason to do so. The three estimators above are not three noisy measurements of the same quantity. They are three distinct mechanistic hypotheses:

- multiplicative reserve-burden accumulation,
- multivariate dysregulation distance,
- weakest-link system limitation.

Without external evidence, averaging them has no special justification. The correct use of these estimators is therefore not as an ensemble, but as competing formulas to be scored under a verification harness. The autoresearch loop should decide which class survives, not an ad hoc aggregation rule.

## 7. Verifiable Criteria for Autoresearch
The central methodological contribution is that candidate formulas can be evaluated without mortality labels if the score is based on structural validity.

Let $R(v,f,h,a)$ be any candidate formula. We define three families of verifiable criteria.

### 7.1 Ordering Criteria
A valid ACM-like estimator should be monotone in the expected directions:

$$
\frac{\partial R}{\partial v} < 0,\quad
\frac{\partial R}{\partial f} > 0,\quad
\frac{\partial R}{\partial h} > 0,\quad
\frac{\partial R}{\partial a} > 0
$$

In addition, for any pair of profiles $x$ and $y$ such that $x$ is clearly healthier than $y$, the formula should satisfy

$$
R(x) < R(y)
$$

This can be tested over thousands of synthetic profile pairs.

### 7.2 Smoothness and Boundedness
A candidate estimator should not exhibit implausible discontinuities. For small perturbations $\Delta$,

$$
\left|R(x+\Delta) - R(x)\right| \le L \left|\Delta\right|
$$

for a chosen smoothness constant $L$. Output should also remain bounded in a plausible range, for example

$$
0 \le R(v,f,h,a) \le 30
$$

when $R$ is expressed as annual percent mortality. Exact bounds are configurable; the key point is that they are explicit and testable.

### 7.3 Invariance and Consistency
Several consistency conditions are especially useful:

- Dominance consistency: if profile $x$ is at least as good as $y$ on all risk dimensions and strictly better on one, then

$$
R(x) < R(y)
$$

- Reference consistency: a designated healthy reference profile should map to a chosen anchor value.
- Transformation consistency: unit conversion should not alter the substantive ranking.

These are not empirical truths about mortality, but they are verifiable structural requirements for any formula purporting to approximate it.

## 8. The Verification Objective
The autoresearch system should optimize formulas against a total score

$$
S(R)=S_{\text{mono}}+S_{\text{pairs}}+S_{\text{smooth}}+S_{\text{bounds}}+S_{\text{consistency}}
$$

where each component penalizes structural violations.

A concrete implementation is:

$$
S_{\text{mono}} =
-\sum_i
\left(
\max\left(\frac{\partial R}{\partial v}(x_i),0\right)
+
\max\left(-\frac{\partial R}{\partial f}(x_i),0\right)
+
\max\left(-\frac{\partial R}{\partial h}(x_i),0\right)
+
\max\left(-\frac{\partial R}{\partial a}(x_i),0\right)
\right)
$$

$$
S_{\text{pairs}} =
-\sum_i \max\left(R(x_i)-R(y_i)+\epsilon,0\right)
$$

for curated healthy-worse pairings $(x_i,y_i)$, and analogous penalties for smoothness, bounds, and consistency.

This turns formula discovery into a search problem with a measurable reward signal. The system need not know true ACM; it only needs to know whether a candidate formula satisfies the desired mathematical behavior.

## 9. Search Space Design
A crucial practical choice is the hypothesis class. If the formula space is too large, the agent will find pathological but formally valid expressions. If too small, it cannot represent useful structure. The recommended search family is therefore explicit, low-dimensional, monotone-constrained, and interpretable.

One suitable class is

$$
R(v,f,h,a)=R_{\max}\,\sigma\!\left(
c_0 + c_1 z_v + c_2 z_f + c_3 z_h + c_4 z_a + c_5 z_f z_h + c_6 z_h z_a
\right)
$$

where

$$
z_v=\frac{35-v}{10},\quad
z_f=\frac{f-80}{40},\quad
z_h=\frac{h-5.4}{0.5},\quad
z_a=\frac{a-80}{30}
$$

and

$$
\sigma(x)=\frac{1}{1+e^{-x}}
$$

with constraints

$$
c_1,c_2,c_3,c_4,c_5,c_6 \ge 0
$$

This family preserves monotonicity in the intended directions and permits explicit interaction terms. The coefficients are not learned from mortality; they are selected by maximizing the structural validity score $S(R)$.

## 10. Interpretation of the Breakthrough
The proposed framework does not solve mortality estimation in the conventional statistical sense. Its contribution is different and, under extreme constraints, arguably more important: it transforms an impossible supervised prediction problem into a tractable constrained scientific search problem.

The breakthrough consists of four moves:

- abandoning direct ACM fitting when it is not identifiable,
- replacing mortality with structurally grounded surrogates,
- making the desired properties of a mortality-like formula explicit and testable,
- using autoresearch to optimize over formula space under those criteria.

This is especially suitable for temporary exploratory contexts, sparse variables, and LLM-guided scientific workflows where outcome data are unavailable but formal reasoning and iterative search are feasible.

## 11. Limitations
The framework has sharp limits. It does not produce validated ACM. It cannot infer absolute mortality without eventual external calibration. Choice of reference values, smoothness penalties, and anchor ranges remains partly normative. The surrogate may be elegant yet wrong. Structural validity is weaker than predictive validity.

However, under the stipulated conditions, these are not flaws of the framework; they are reflections of the information-theoretic limits of the problem. Any method that claims more without external anchors is concealing assumptions rather than removing them.

## 12. Future Work
Several extensions follow naturally.

First, the synthetic verification suite can be greatly expanded using expert-curated physiological comparisons, adversarial edge cases, and symbolic derivative checks. Second, the candidate variable set can be generalized from four markers to arbitrary sparse biomedical vectors. Third, repeated-measures variables can enable stronger surrogates based on dynamical resilience rather than static burden. Fourth, once even weak mortality-linked data become available, the structurally selected formula can be calibrated rather than reinvented.

Finally, LLM-based autoresearch systems can use this framework to iteratively propose, test, and refine mechanistic scoring rules in settings where conventional dataset-driven epidemiology is impossible.

## 13. Conclusion
When mortality labels, age, life tables, external hazard ratios, and case-control data are all unavailable or unacceptable, direct ACM estimation is not credible. Yet scientific progress remains possible if one stops treating the problem as supervised prediction and instead treats it as constrained formula discovery. The most promising latent targets are physiologic reserve, homeostatic dysregulation, and multi-system slack. Candidate ACM-like formulas can then be evaluated not by outcome fit, but by a verification harness based on monotonicity, dominance, smoothness, boundedness, and invariance. This creates a principled objective for autoresearch systems and yields explicit, auditable formulas suitable for later calibration. The result is not mortality truth, but a rigorously structured approximation scaffold: a necessary first stage in settings where outcome-grounded modeling is impossible.

## Appendix A. Minimal Example of a Verification Harness
Given a candidate $R(v,f,h,a)$, define profile pairs such as:

$$
x_1=(50,50,5.0,60), \quad y_1=(20,180,6.4,150)
$$

$$
x_2=(42,70,5.2,75), \quad y_2=(30,120,5.8,110)
$$

and require $R(x_i)<R(y_i)$ for all such pairs.

Then sample random profiles over a plausible domain, for example:

$$
15 \le v \le 70,\quad
20 \le f \le 250,\quad
4.5 \le h \le 9.0,\quad
40 \le a \le 200
$$

Check derivative signs numerically, evaluate local perturbation stability, and penalize formulas that violate any rule. The best formula is the one that maximizes the total structural validity score, not the one that merely looks reasonable.

## Appendix B. Recommended Positioning for Downstream LLM Context
For downstream use, the methodology can be summarized as follows:

> We cannot estimate true ACM from sparse biomarkers without mortality-linked external anchors. Instead, we search for an explicit ACM-like surrogate formula over biomarker space. Candidate formulas are evaluated against a verification harness enforcing monotonicity, dominance, smoothness, boundedness, and invariance. The preferred latent constructs are physiologic reserve, homeostatic dysregulation, and multi-system slack. The output is a structurally valid surrogate suitable for later calibration, not a claim of true mortality prediction.

If you want, I can turn this into a more polished Nature-style, arXiv-style, or plain technical memo version.
