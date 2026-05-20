9706 IEEE INTERNET OF THINGS JOURNAL, VOL. 8, NO. 12, JUNE 15, 2021

> Attacking and Protecting Data Privacy in Edge–Cloud Collaborative
> Inference Systems
>
> Zecheng H[e ,](https://orcid.org/0000-0003-2639-2826) *Student*
> *Member,* *IEEE*, Tianwei Zhan[g
> ,](https://orcid.org/0000-0001-6595-6650) and Ruby B. Le[e
> ,](https://orcid.org/0000-0001-9497-0777) *Life* *Fellow,* *IEEE*

***Abstract*—Beneﬁting** **from** **the** **advance** **of** **deep**
**learning** **(DL)** **technology,** **Internet-of-Things** **(IoT)**
**devices** **and** **systems** **are** **becoming** **more**
**intelligent** **and** **multifunctional.** **They** **are**
**expected** **to** **run** **various** **DL** **inference** **tasks**
**with** **high** **efﬁciency** **and** **performance.** **This**
**requirement** **is** **challenged** **by** **the** **mismatch**
**between** **the** **limited** **computing** **capability** **of**
**edge** **devices** **and** **large-scale** **deep** **neural**
**networks.** **Edge–cloud** **collaborative** **systems** **are**
**then** **introduced** **to** **mitigate** **this** **conﬂict,**
**enabling** **resource-constrained** **IoT** **devices** **to**
**host** **arbitrary** **DL** **applica-tions.** **However,** **the**
**introduction** **of** **third-party** **clouds** **can** **bring**
**potential** **privacy** **issues** **to** **edge** **computing.**
**In** **this** **article,** **we** **con-duct** **a** **systematic**
**study** **about** **the** **opportunities** **of** **attacking**
**and** **protecting** **the** **privacy** **of** **edge–cloud**
**collaborative** **systems.** **Our** **contributions** **are**
**twofold:** **1)** **we** **ﬁrst** **devise** **a** **set** **of**
**new** **attacks** **for** **an** **untrusted** **cloud** **to**
**recover** **arbitrary** **inputs** **fed** **into** **the**
**system,** **even** **if** **the** **attacker** **has** **no**
**access** **to** **the** **edge** **device’s** **data** **or**
**computations,** **or** **permissions** **to** **query** **this**
**system** **and** **2)** **we** **empirically** **demonstrate**
**that** **solutions** **that** **add** **noise** **fail** **to**
**defeat** **our** **proposed** **attacks,** **and** **then**
**propose** **two** **more** **effective** **defense** **methods.**
**This** **provides** **insights** **and** **guidelines** **to**
**develop** **more** **privacy-preserving** **collaborative**
**systems** **and** **algorithms.**

***Index*** ***Terms*—Artiﬁcial** **intelligence,** **collaborative**
**inference,** **edge–cloud** **computing,** **security** **and**
**privacy.**

> I. INTRODUCTION
>
> ECENT years have witnessed the rapid development of deep learning (DL)
> and Internet-of-Things (IoT)

technologies. IoT devices become appealing targets for DL applications.
They use various sensors (e.g., cameras, micro-phones, and gyroscopes)
to collect data and information from environmental contexts, run the DL
applications to interpret sensory data, and make control decisions. The
integration of AI and IoT leads to the era of Artiﬁcial Intelligence of
Things (AIoT), which has signiﬁcantly changed our daily life:
small-scaled AIoT systems are introduced to build smart homes and
increase the comfort and quality of life; medium-scale AIoT

Manuscript received May 18, 2020; revised July 18, 2020; accepted August
20, 2020. Date of publication September 8, 2020; date of current version
June 7, 2021. This work was supported in part by NSF STARSS under Grant
1526493, and in part by a research gift from Siemens. The work of
Tianwei Zhang was supported by Singapore MoE AcRF Tier1 under Grant
RS02/19. The work of Ruby B. Lee was supported by the Qualcomm Faculty
Award. This article was presented in part at the 35th Annual Computer
Security Applications Conference (ACSAC’19), San Juan, PR, USA, Dec.
2019. *(Corresponding* *author:* *Ruby* *B.* *Lee.)*

Zecheng He and Ruby B. Lee are with the Department of Electrical
Engineering, Princeton University, Princeton, NJ 08540 USA (e-mail:
zechengh@princeton.edu; rblee@princeton.edu).

Tianwei Zhang is with the School of Computer Science and Engineering,
Nanyang Technological University, Singapore 639798 (e-mail: tianwei.
zhang@ntu.edu.sg).

> Digital Object Identiﬁer 10.1109/JIOT.2020.3022358

systems are deployed in warehouses and factories for higher efﬁciency
and automation; and large-scale AIoT systems can contribute to the
establishment of smart cities.

Deploying DL inference applications on commodity edge devices has
several challenges. On one hand, an IoT device can collect streaming
information at a very high rate (e.g., vehicle detection \[2\], remote
monitoring \[3\], scene analysis \[4\], and application trace analysis
\[5\]). This requires the device to run the DL models and analyze the
data at a high speed. On the other hand, state-of-the-art DL models are
becoming more complicated with larger sizes, making it infeasible for
resource-constrained IoT devices to satisfy the performance
requirements: the limited computation resources of the device
cancausesigniﬁcantlatency;thelimitedstoragecapacitymakes it hard to
store a large deep neural network (DNN) model; and
thelimitedbatterycapacitycausesacriticalenergyconsumption constraint.

To overcome this challenge, one possible approach is to ofﬂoad the
entire DL model and inference computation to the cloud. The edge device
sends the input data to the cloud and receives the output. While this
can resolve the aforementioned limitations of edge devices, it incurs
signiﬁcant communication costs when sending a large volume of raw data.
Besides, there can be privacy breaches of the inference data \[6\],
especially if the input data are highly sensitive such as patients’
records, and integrity breaches of the model \[7\], if the cloud is not
trusted.

An optimized strategy is to adopt collaborative inference between the
edge devices and the cloud \[8\]–\[12\]. The DL model can be divided
into two parts. The ﬁrst few layers of the network are stored in the
local edge device, while the rest are ofﬂoaded to a remote cloud. Given
an input, the edge device calculates the output of the ﬁrst layers,
sends it to the cloud, and retrieves the ﬁnal results. This approach can
reduce communication costs, as the intermediate output can be designed
to be much smaller than the raw input. Such low data transfer bandwidth
also achieves lower latency and smaller energy consumption.
Collaborative inference makes it feasible and efﬁcient to deploy
large-scale intelligent workloads on today’s edge platforms.

This article presents an investigation of inference data privacy in
edge–cloud collaborative systems, from the perspec-tives of attacks and
defenses. Prior works all aimed to improve the performance and efﬁciency
of such systems, while ignor-ing potential security issues. To the best
of our knowledge, we are the ﬁrst to demonstrate the feasibility of
input data privacy

> 2327-4662 2020 IEEE. Personal use is permitted, but
> republication/redistribution requires IEEE permission. See
> https://www.ieee.org/publications/rights/index.html for more
> information.
>
> Authorized licensed use limited to: Universiteit van Amsterdam.
> Downloaded on May 19,2026 at 12:04:50 UTC from IEEE Xplore.
> Restrictions apply.

<img src="./ed5wty2f.png"
style="width:1.59722in;height:1.15191in" />HE *et* *al.*: ATTACKING AND
PROTECTING DATA PRIVACY IN EDGE–CLOUD COLLABORATIVE INFERENCE SYSTEMS
9707<img src="./gjbotesf.png"
style="width:0.12847in;height:0.11024in" /><img src="./jvij01ir.png"
style="width:1.30642in;height:0.88021in" /><img src="./5gnlo0i2.png"
style="width:0.12587in;height:0.1059in" /><img src="./kmo0m24u.png"
style="width:0.13368in;height:0.10764in" />

Fig. 1. (a) DNN model deployed in (b) collaborative edge–cloud system.

attacks against cloud-edge collaborative inference systems. The data
privacy considered in this article is the conﬁdentiality of the raw
inputs.

Two key questions are considered in this study. The ﬁrst one is: *if*
*the* *cloud* *is* *malicious* *or* *compromised,* *can* *the*
*attacker* *recover* *raw* *input* *data,* *otherwise* *available*
*only* *to* *the* *edge* *device?* Past work claimed the edge–cloud
collaborative infer-ence can provide better privacy protection, as the
cloud only receives the intermediate values instead of the raw data
\[10\]. We show that an untrusted cloud can still easily and accurately
recover the sensitive data from the intermediate values without
accessing the edge-side model.

We design a set of novel attack techniques to achieve this goal under
different settings. First, for a white-box attacker, we propose using
regularized maximum likelihood estimation (rMLE) to recover the samples
from the model parameters and intermediate values. Second, for a
black-box attacker, we propose the inverse-network attack to identify
the reverse mapping from the intermediate outputs to inputs without the
knowledge of model information. Third, we consider the most limited
adversarial capability where the cloud has no knowl-edge of the target
model and is not allowed to query the model. Conducting privacy attacks
under this setting is extremely dif-ﬁcult, and this threat model is
rarely considered in past work. For these query-free attacks, we
introduce a new method of shadow model reconstruction to achieve this
attack.

The second question we address in this article is: *how* *can* *the*
*edge* *devices* *mitigate* *privacy* *leakage* *from* *the* *untrusted*
*cloud?* Past work adopted differential privacy to protect the inference
data \[13\]. We show that this approach is imprac-tical against our
proposed attacks as it brings unacceptable performance degradation to
the DL models. Instead, we pro-pose two novel strategies that can better
thwart privacy attacks while still maintaining good model performance.
The ﬁrst one is *the* *dropout* *defense*: by deactivating random
neurons during the inference, the adversary is not able to precisely
generate the original images from the intermediate values. Our second
defense is *privacy-aware* *DNN* *partitioning*: we com-prehensively
evaluate different factors that can affect the attack results and
propose some guidelines to partition the DL mod-els for better privacy.
We hope our ﬁndings can guide machine learning researchers and
practitioners to design more secure collaborative inference systems.

> The key contributions of this article are as follows.
>
> 1\) A systematic study of attacks and defenses for infer-ence data
> privacy in edge–cloud collaborative machine learning systems.
>
> 2\) Three attack approaches to recover inference data under different
> settings.
>
> 3\) Two new defense approaches to prevent inference data leakage to
> the untrusted cloud.

The remainder of this article is organized as follows. Section II
presents the edge–cloud system model, threat model, and experimental
conﬁgurations. Section III describes attacks under white-box, black-box,
and query-free settings, includ-ing attack approaches, implementations,
and evaluation results. Section IV discusses possible mitigation
solutions. We give related work in Section V and conclude in Section VI.

> II\. PRELIMINARIES

A DNN is a parameterized function *fθ* : *X* → *Y* that maps an input
tensor *x* ∈ *X* to an output tensor *y* ∈ *Y* \[Fig. 1(a)\]. It
consists of an input layer, an output layer, and a sequence of hidden
layers between the input and output layers. Each layer is a collection
of units called *neurons*, which are con-nected to other neurons in the
previous layer and the next layer. Each connection between the neurons
can transmit a signal to another neuron in the next layer. In this way,
a neural network transforms the inputs through hidden layers to the
outputs, by applying operations (e.g., a linear function or elementwise
nonlinear activation function) in each layer.

*A.* *System* *Model*

In an edge–cloud collaborative inference system \[Fig. 1(b)\], a DNN is
partitioned into two parts: *fθ* = *fθ*1 ◦ *fθ*2. Each part contains
several layers. The edge device hosts the ﬁrst part *fθ*1. It collects
inference data from the environment, generates the intermediate value
*v* = *fθ*1*(x)*, and sends it to the cloud. The cloud hosts the second
part of the model *fθ*2. When receiving the intermediate value *v* from
the edge device, it calculates the ﬁnal output *y* = *fθ*2*(v)* and
returns it to the edge device.

Determining a way to partition the DNN model is nontrivial. Different
factors must be considered to identify the optimal strategy.

> 1\) *Latency:* An optimal partition should give the fastest inference
> speed. The latency is determined by the infer-ence time on the edge
> device, the cloud, as well as the network transmission time. The cloud
> can process the inference at a much faster speed. So it is prefer-able
> to move more DNN layers to the cloud. However, this can cause larger
> volumes of transmitted data and longer network latency. So the
> performance of edge devices, cloud servers, and network transmission
> must be balanced.
>
> 2\) *Power:* An optimal partition should be energy efﬁcient. This is
> particularly important for edge devices that have limited power
> capabilities. The energy consumed by the edge device consists of the
> inference computation (determined by the number of layers) and network
> com-munication (determined by the size of transmitted data). Similar
> to latency optimization, the energy consumption of these two parts
> needs to be balanced.
>
> 3\) *Memory* *Size:* When conducting inference, the device needs to
> load the entire DNN *fθ*1 into the memory.
>
> Authorized licensed use limited to: Universiteit van Amsterdam.
> Downloaded on May 19,2026 at 12:04:50 UTC from IEEE Xplore.
> Restrictions apply.

9708 IEEE INTERNET OF THINGS JOURNAL, VOL. 8, NO. 12, JUNE 15,
2021<img src="./22vhqkhh.png" style="width:0.36632in" /><img src="./ryc254uy.png" style="width:0.35503in" /><img src="./vz4eujlz.png" style="width:0.2092in" /><img src="./gyb0u40j.png" style="width:0.12934in" /><img src="./pssfwpjj.png" style="width:0.57118in" /><img src="./aut3azor.png"
style="width:5.63586in;height:1.38867in" />

> TABLE I TABLE OF NOTATIONS
>
> <img src="./exa2ikzy.png" style="width:0.36111in" /><img src="./d0vw0yet.png"
> style="width:1.67882in;height:1.26321in" /><img src="./tyht2pjy.png" style="width:0.88261in" /><img src="./gaoylcxw.png" style="width:0.17795in" /><img src="./da0nz52m.png" style="width:0.36198in" /><img src="./esmhppnu.png"
> style="width:1.6784in;height:1.26321in" /><img src="./h04uaeuv.png" style="width:0.88263in" /><img src="./k1alwvbv.png" style="width:0.17795in" /><img src="./r0mtcobw.png" style="width:0.25in" /><img src="./olw0mqzm.png" style="width:0.17882in" /><img src="./rde2caf5.png" style="width:0.23264in" /><img src="./qhxplryv.png" style="width:0.26997in" /><img src="./jazvgj1p.png"
> style="width:0.21094in;height:0.19097in" /><img src="./b5onz2qz.png" style="width:0.31858in" /><img src="./c4grwfjt.png"
> style="width:0.53363in;height:0.19097in" /><img src="./tdb1z4de.png" style="width:0.28733in" /><img src="./eokxbvzo.png" style="width:0.33681in" /><img src="./rtv12zut.png"
> style="width:3.42337in;height:0.88082in" />TABLE II EXPERIMENT
> CONFIGURATIONS

Fig. 2. Breakdown of inference latency (left) and energy consumption
(right) in edge–cloud systems. Data are from \[9\].

> Some edge devices are equipped with limited memory resources, and
> incapable of hosting too many network layers. This gives another
> constraint when selecting the optimal split point.

With these considerations, DNN partitioning is usually for-mulated as an
optimization problem \[8\]–\[12\]. Fig. 2 shows the comparisons of
latency and energy consumption between edge–cloud, cloud-only, and
edge-only solutions (data are collected from \[9\]). We capture the
results from Fig. 6 in Neurosurgeon \[9\]. In Neurosurgeon \[9\], a
detailed study of latency and power consumption in a typical edge–cloud
collab-orative system was evaluated. An AlexNet model is deployed
between a mobile device and a cloud connected by WiFi. We observe that
with an optimal split point, an edge–cloud system can achieve lower
latency and energy than a cloud-only or an edge-only system: by
ofﬂoading some DNN layers to the cloud, the processing time and energy
consumed on the device is less than the edge-only system. Meanwhile, as
the size of the intermediate data is smaller than the original input,
the latency and energy costs of network transmission in the edge–cloud
system are also less than the cloud-only system.

In practice, most layers (including all fully connected layers) are
commonly ofﬂoaded to the cloud, while the edge device only computes a
small number of convolutional layers for fea-ture extraction, due to
power and resource constraints \[9\]. This gives a chance for an
untrusted cloud provider to steal sensitive inference input, which we
will discuss below.

*B.* *Threat* *Model*

We consider a collaborative inference system between the edge device E
and cloud C. The target model is split into two parts: *fθ* = *fθ*2
◦*fθ*1. E performs the ﬁrst few layers *fθ*1, while C performs the rest
of the layers *fθ*2. We consider E is trusted:

when input is fed into *fθ*1, E correctly processes it and never leaks
it to other parties. However, C is untrusted, attempting to steal the
input. We consider the conﬁdentiality of an individual raw input when we
use the term “data privacy” throughout this article. Other forms of data
privacy, e.g., membership or linkability, are not in our threat model.

We assume C strictly follows the collaborative inference protocol:
receiving *v* = *fθ*1*(x)* from E and generating *y* = *fθ*2*(v)*. C
cannot compromise the inference process con-ducted by E, and has no
knowledge of the input *x*, nor any intermediate values inside E, except
*v*. We consider adversaries with different capabilities:

> 1\) *White* *Box:* C has the knowledge of the model at the edge side
> *fθ*1, including its network structure and parameters.
>
> 2\) *Black* *Box:* C does not have knowledge of *fθ*1, but is able to
> query the model *fθ*1. The adversary does not need to know the exact
> training data, but he can collect the same type of samples as the
> training data. This assumption is reasonable in practice, e.g., the
> adversary can collect arbitrary face samples for a face recognition
> model or medical records for a diagnostic system.
>
> 3\) *Query* *Free:* C does not have knowledge of *fθ*1, or the
> permission to query the model *fθ*1. This type of attacks has the
> minimum attacker capability. Similar to the black-box attack, we
> assume the attacker can collect samples similar in type to the
> training data.

*C.* *Notations* *and* *Experimental* *Conﬁgurations*

We summarize our notations in Table I. We show detailed conﬁgurations of
experiments in Table II.

Our attacks and defenses are generic and applicable to vari-ous data
sets. In this article, we demonstrate the attack results on the MNIST
data set and the defense results on MNIST and CIFAR10. More details on
the attacks can be found in \[1\].

> Authorized licensed use limited to: Universiteit van Amsterdam.
> Downloaded on May 19,2026 at 12:04:50 UTC from IEEE Xplore.
> Restrictions apply.

<img src="./w5re11rs.png"
style="width:0.28033in;height:0.28033in" /><img src="./edgz3xt0.png"
style="width:0.282in;height:0.28033in" /><img src="./wi5zxmfh.png"
style="width:0.28033in;height:0.28033in" /><img src="./yu01x2ol.png"
style="width:0.28033in;height:0.28033in" /><img src="./izt1w5kq.png"
style="width:0.282in;height:0.28033in" /><img src="./c0bpg0ph.png"
style="width:0.28033in;height:0.28033in" /><img src="./sa204szg.png"
style="width:0.282in;height:0.28033in" /><img src="./gv2431jv.png"
style="width:0.28033in;height:0.28033in" /><img src="./a3dikomx.png"
style="width:0.282in;height:0.28033in" /><img src="./3xsmuau0.png"
style="width:0.28033in;height:0.28033in" />HE *et* *al.*: ATTACKING AND
PROTECTING DATA PRIVACY IN EDGE–CLOUD COLLABORATIVE INFERENCE SYSTEMS
9709<img src="./vz0cwltd.png"
style="width:0.28033in;height:0.28033in" /><img src="./assmd2ly.png"
style="width:0.282in;height:0.28033in" /><img src="./4owd1iwm.png"
style="width:0.28033in;height:0.28033in" /><img src="./cfwcjdcy.png"
style="width:0.28033in;height:0.28033in" /><img src="./l5rr3tsr.png"
style="width:0.282in;height:0.28033in" /><img src="./qfxikrqj.png"
style="width:0.28033in;height:0.28033in" /><img src="./y12yvyac.png"
style="width:0.282in;height:0.28033in" /><img src="./fqmvzhxg.png"
style="width:0.28033in;height:0.28033in" /><img src="./pkexo0ou.png"
style="width:0.282in;height:0.28033in" /><img src="./0fsvjx3i.png"
style="width:0.28033in;height:0.28033in" /><img src="./5i5fefbh.png"
style="width:0.28033in;height:0.282in" /><img src="./t4vnflyc.png" style="width:0.282in;height:0.282in" /><img src="./4xsmaukt.png"
style="width:0.28033in;height:0.282in" /><img src="./lxq50zof.png"
style="width:0.28033in;height:0.282in" /><img src="./svo1jjrr.png" style="width:0.282in;height:0.282in" /><img src="./vo5aug4d.png"
style="width:0.28033in;height:0.282in" /><img src="./ccw0h03v.png"
style="width:0.28033in;height:0.282in" /><img src="./bw0lgttf.png" style="width:0.282in;height:0.282in" /><img src="./lgpwdqph.png"
style="width:0.28033in;height:0.282in" />

The ﬁrst victim model we target is LeNet5. It consists of two
convolutional layer blocks (each block has a convolu-tional layer, an
activation layer, and a pooling layer), three fully connected layers,
and one softmax layer. The model can be split at either the ﬁrst
convolutional layer or the second convolutional layer after activation.
These conﬁgurations are realistic in edge–cloud scenarios, as the heavy
computational layers (including all fully connected layers) are ofﬂoaded
to the cloud.

We follow the standard MNIST and CIFAR10 split for train-ing and testing
samples \[14\]. We set the learning rate to 10−3 and choose ADAM as our
optimizer. The target model, all attack techniques, and defense
solutions are implemented with Pytorch 1.0.1. We run our experiments on
a server with one Nvidia 1080Ti GPU and two Intel Xeon E5-2667 CPUs.

To quantify the effectiveness of attacks and defenses, we adopt two
metrics, peak signal-to-noise ratio (PSNR) \[15\] and structural
similarity index (SSIM) \[16\]. Larger values of these two metrics
indicate the recovered input is of higher quality, and more similar to
the original one.

III\. ATTACK METHODOLOGIES *A.* *White-Box* *Attack*

We start from the white-box setting, where the adversarial cloud knows
the parameters of the initial layers *fθ*1 on the edge device. Formally,
the problem we consider is: *how* *can* *the* *adversary* *recover* *an*
*input* *x*0*,* *from* *the* *corresponding* *intermediate* *value*
*fθ*1*(x*0*),* *and* *the* *model* *parameters* *θ*1*?* We propose rMLE
to solve this problem.

*rMLE:* We treat the attack as an optimization problem: given
*fθ*1*(x*0*)*, our goal is to ﬁnd a generated sample *x*, which
sat-isﬁes two requirements: 1) the intermediate output of this sample
*fθ*1*(x)* is similar to *fθ*1*(x*0*)* and 2) *x* is a natural sample,
following the same distribution as other inference samples.

For requirement (1), we use the Euclidean distance (ED) to measure the
similarity between *fθ*1*(x)* and *fθ*1*(x*0*)* \[(1a)\]. Note that
*fθ*1*(x)* can be interpreted as the mapping from the input space
(unobservable to the adversary) to the feature space (observable to the
adversary). Then, this ED represents the *posteriori* information from
the adversary’s intermediate-level observation. Our goal is to ﬁnd the
optimal sample *x* that minimizes this distance.

For requirement (2), we adopt the *total* *variation* \[17\] to
represent the *prior* information of an input sample. The total
variation of a 2-D image *x* is deﬁned in (1b), where *xi,j* represents
the pixel at position *(i,j)*. *β* is a parameter that con-trols the
smoothness of the image. Larger *β* results in more piecewise-smoothed
images. We set *β* = 1*.*0 throughout our experiments. Minimization of
this metric can guarantee the generated image *x* is piecewise smooth,
i.e., avoiding drastic variations inside regions but allowing large
changes along the region boundaries

> *ED(x,x*0*)* = k*fθ*1*(x)* −*fθ*1*(x*0*)*k2 (1a) *TV(x)* = X
> *xi*+1*,j* −*xi,j*2 +*xi,j*+1 −*xi,j*2 *β/*2 (1b)
>
> *i,j*
>
> *x*∗ = argmin*x* *ED(x,x*0*)*+*λTV(x).* (1c)

Fig. 3. Recovered inputs in white-box attacks.

The total objective function of the model inversion problem is a
combination of feature space similarity and input smooth-ness, as shown
in (1c). In this equation, *λ* is a hyperparameter to balance the
effects of the two terms. If the feature space, *fθ*1*(x)* is far from
the input space, i.e., a lot of network lay-ers are computed on the
trusted participant E, a large *λ* is required because less posterior
information about the input can be recovered from the feature space and
the adversary needs to rely on the prior information. In contrast, if
only a small number of layers are deployed on E, then the adversary only
needs to select a small *λ*. We set *λ* = 0 when getting the inverse
from layers before the ﬁrst fully connected layer, and *λ* = 0*.*1 when
getting the inverse from layers after the ﬁrst fully connected layer. We
perform gradient descent (GD) to solve (1c) and recover the image.

*Evaluation:* Fig. 3 shows the white-box attack results. The ﬁrst row
shows the original inference samples and the remain-ing rows are the
recovered images when the split point is at different layers. We observe
that the adversary can accurately recover the images with high ﬁdelity
when the split point is either at the ﬁrst (conv1) or last (ReLU2)
convolutional layer. At the ﬁrst split layer, PSNR is 39.69 dB and SSIM
is 1.00. At the last split layer, PSNR is 15.10 dB and SSIM is 0.60.1
This indicates that when the split point is at a deeper layer, the
quality and similarity of recovered images become worse.

*B.* *Black-Box* *Attacks*

Next, we consider the black-box setting, where the adver-sary does not
have knowledge of the structure or parameters of *fθ*1. We assume that
the adversary can query the black-box model: he can send an arbitrary
input *x* to E and observe the corresponding output *fθ*1*(x)*.

Data privacy attacks under the black-box setting are more challenging
because, without the knowledge of model param-eters, the adversary
cannot directly perform a GD on *fθ*1 to solve the optimization problem
in (1c). One solution is to ﬁrst recover the model structure and
parameters by querying the model, and then recover the inference
samples. The possibility of model reconstruction has been demonstrated
in \[18\]–\[20\].

We propose a more efﬁcient approach, the inverse network, to directly
identify the inversed mapping from output to input, without the model
information. Our solution is easier to implement and can recover inputs
with higher ﬁdelity.

*Inverse* *Network:* Conceptually, the inverse network is the
approximated inverse function of *fθ*1, trained with *v* = *fθ*1*(x)* as
input, and *x* as output. The attack consists of three phases:

1In our experiments, we observe that PSNR*\>*10 dB or SSIM*\>*0.3 are
con-sidered as good quality because the inversed images are visually
recognizable by the adversary.

> Authorized licensed use limited to: Universiteit van Amsterdam.
> Downloaded on May 19,2026 at 12:04:50 UTC from IEEE Xplore.
> Restrictions apply.

9710<img src="./w123cgz1.png"
style="width:0.28033in;height:0.28033in" /><img src="./gekugx02.png"
style="width:0.282in;height:0.28033in" /><img src="./fgey5y3n.png"
style="width:0.28033in;height:0.28033in" /><img src="./1arq5sls.png"
style="width:0.282in;height:0.28033in" /><img src="./2f1pke3c.png"
style="width:0.28033in;height:0.28033in" /><img src="./xog4ux2t.png"
style="width:0.28033in;height:0.28033in" /><img src="./30yld0yp.png"
style="width:0.28033in;height:0.28033in" /><img src="./ibsdssad.png"
style="width:0.28033in;height:0.28033in" /><img src="./0xyu3ds2.png"
style="width:0.282in;height:0.28033in" /><img src="./0rz5wwue.png"
style="width:0.28033in;height:0.28033in" /><img src="./sattdhko.png"
style="width:0.28033in;height:0.28033in" /><img src="./3vwclyld.png"
style="width:0.282in;height:0.28033in" /><img src="./qqcm2l4x.png"
style="width:0.28033in;height:0.28033in" /><img src="./epichi1q.png"
style="width:0.282in;height:0.28033in" /><img src="./xipb5aos.png"
style="width:0.28033in;height:0.28033in" /><img src="./csgqgjeg.png"
style="width:0.28033in;height:0.28033in" /><img src="./30xkmtsk.png"
style="width:0.28033in;height:0.28033in" /><img src="./bjnnzbco.png"
style="width:0.28033in;height:0.28033in" /><img src="./vrwpjc4p.png"
style="width:0.282in;height:0.28033in" /><img src="./jxdep5oo.png"
style="width:0.28033in;height:0.28033in" /><img src="./fcrnh555.png"
style="width:0.28033in;height:0.282in" /><img src="./2oo0wnf3.png" style="width:0.282in;height:0.282in" /><img src="./fzopld2f.png"
style="width:0.28033in;height:0.282in" /><img src="./qzzygjqo.png" style="width:0.282in;height:0.282in" /><img src="./pllcebdt.png"
style="width:0.28033in;height:0.282in" /><img src="./mtswn4fo.png"
style="width:0.28033in;height:0.282in" /><img src="./151qr1fc.png"
style="width:0.28033in;height:0.282in" /><img src="./ww524p2s.png"
style="width:0.28033in;height:0.282in" /><img src="./ruppzm1y.png" style="width:0.282in;height:0.282in" /><img src="./dz14s3mr.png"
style="width:0.28033in;height:0.282in" />

Fig. 4. Recovered inputs in black-box attacks.

1\) generating a training set for the inverse network; 2) training the
inverse network; and 3) recovering the input sample by querying the
inverse network.

First, the adversary generates a bag of samples *X* = *(x*1*,* *x*2*,*
*...,xm)* of the same type as the training data to query the target
system, and observes the corresponding intermediate outputs *V* =
*(fθ*1*(x*1*),fθ*1*(x*2*),...,* *fθ*1*(xm))*. Next, he can directly
train an inverse network *f* using *V* as the training input and *X* as
the training output. We initialize the inverse network with the Xavier
initialization \[21\], to avoid the neuron activations in the saturated
or dead regions in the beginning. We leverage *l*2 norm in the pixel
space as the loss function (2), and stochastic GD (SGD) to train the
inverse network

> *f*−1 = argmin*g* 1 Xk*g((fθ*1*(xi))*−*xi)*k2 (2) *i*=1

where *g* is the inverse network to be optimized. Note that the
architecture of the inverse network need not be related to the target
model *fθ*1. In our experiment, we use an entirely

different network architecture.

> Once the inverse network *f*−1 is obtained, the adversary can

recover any inference sample from the intermediate layer out-put: *x* =
*f*−1*(v)*. This approach is more efﬁcient than rMLE:

1\) for each target sample, the adversary only needs to pass through the
inverse network once, while in rMLE, an iterative process is required to
solve the optimization problem and 2) calculating the inversed input is
parameter-free, while rMLE requires tuning the parameters *λ* and *β* in
(1).

*Evaluation:* Fig. 4 shows the recovered images of MNIST. We can observe
that the adversary can recover the input under the black-box setting
with very high quality (PSNR is 40.72 and 20.81 dB for the two split
points) and similarity (SSIM is 0.99 and 0.80 for the two points).

*C.* *Query-Free* *Attacks*

> The inverse-network approach requires the adversary to be

able to query the target model, and generate the data set for training
*f*−1. In this section, we consider the query-free setting,

where the adversary cannot query the model at the edge side and does not
know the model information. The basic idea is that the adversary ﬁrst
reconstructs a shadow model, which imitates the target model’s behavior,
and then uses rMLE over this shadow model to recover the input samples.

*Shadow* *Model* *Reconstruction:* The problem at the ﬁrst step is: how
can the adversary reconstruct a shadow model of the former model layers
*fθ*1 with only the knowledge of the latter layers *fθ*2 and the same
type of training data as *S*? He cannot query the model with speciﬁed
samples to get the intermediate values.

> IEEE INTERNET OF THINGS JOURNAL, VOL. 8, NO. 12, JUNE 15, 2021

The key insight of our approach is that if the shadow model is
reconstructed as *f*0 , it should be able to classify the input with
high accuracy when combined with the later layers *fθ*2

> *yi* ∼ *fθ*2*(fθ*1*(xi))* ∼ *fθ*2*fθ*1*(xi),*for *(xi,yi)* ∈ *S.* (3)

Then, the task of model reconstruction can be translated into minimizing
the classiﬁcation error of the composition of the two models: *fθ*2*(f*0
*(xi))* versus *yi*. Equation 4 shows the loss function for training the
model, where *m* is the number of sam-ples in *S*, *CrossEntropy* is the
cross-entropy loss. Equivalently, this means the training process of
*f*0 is supervised at the output layer of *fθ*2. Once the model *f*0 is
reconstructed, the adversary can perform data recovery attacks using the
rMLE technique in Section III-A

> *fθ*1 = argmin*g* 1 *m* *i*=1
>
> CrossEntropy*(fθ*2*(g(xi)),yi)* (4)
>
> CrossEntropy*y*ˆ*,y* = −X*yc*log*y*ˆ*c* (5) *c*=1

where *C* is the number of classes of the task.

There are two phases in our approach: 1) ofﬂine shadow model
reconstruction and 2) online model inversion. The shadow model
reconstruction only needs to be performed once. Then, all the input
samples can be recovered using the same shadow model, by only one
inference for each input. In the shadow model reconstruction phase, the
adversary can adopt the same type of samples as the training data. He
may not know the original network structure *fθ*1, but he can use an
alternative one for the shadow model. We assume that both the target
model and the shadow model are convolutional neural networks, but with
different numbers of layers and ﬁlters, as well as ﬁlter sizes.

After the training set and network structure are determined, the
adversary can adopt SGD to optimize the loss function of the composition
of the two models. We choose the cross-entropy loss because it performs
well on image classiﬁcation tasks. Other loss functions can be
leveraged, if the adversary aims to ﬁnd inverses of the DNN for
different tasks. Once the shadow model is obtained, the adversary can
use rMLE to recover the inputs.

*Evaluation:* We illustrate the recovered images under the query-free
setting in Fig. 5. The adversary can still recover the input images from
conv1 and ReLU2 layers. The PSNRs for these two split points are 17.86
and 8.03 dB, while the SSIMs are 0.64 and 0.38, respectively. The
quality of the images is relatively lower than the ones in the white-box
or black-box setting, indicating the query-free attacks are harder to
achieve. This is straightforward, as the adversary now has smaller
capa-bilities. Also, more layers on the edge device can also increase
the difﬁculty of image recovery.

> IV\. DEFENSE METHODOLOGIES

Given the severity of inference privacy attacks in edge– cloud
collaborative systems, we aim to explore defense meth-ods in this
section. We ﬁrst empirically evaluate one common

> Authorized licensed use limited to: Universiteit van Amsterdam.
> Downloaded on May 19,2026 at 12:04:50 UTC from IEEE Xplore.
> Restrictions apply.

HE *et* *al.*: ATTACKING AND PROTECTING DATA PRIVACY IN EDGE–CLOUD
COLLABORATIVE INFERENCE SYSTEMS 9711<img src="./jixdjued.png"
style="width:0.28033in;height:0.28033in" /><img src="./bwbgvash.png"
style="width:0.282in;height:0.28033in" /><img src="./eehafesz.png"
style="width:0.28033in;height:0.28033in" /><img src="./u3hpk32y.png"
style="width:0.282in;height:0.28033in" /><img src="./zdck3mbn.png"
style="width:0.28033in;height:0.28033in" /><img src="./xlg3lgch.png"
style="width:0.28033in;height:0.28033in" /><img src="./vwbbuhe5.png"
style="width:0.28033in;height:0.28033in" /><img src="./we2lsupk.png"
style="width:0.28033in;height:0.28033in" /><img src="./yfjdem5n.png"
style="width:0.282in;height:0.28033in" /><img src="./lreord45.png"
style="width:0.28033in;height:0.28033in" /><img src="./c52rmhjm.png"
style="width:0.28033in;height:0.28033in" /><img src="./rqy03gro.png"
style="width:0.282in;height:0.28033in" /><img src="./ffpj5dbs.png"
style="width:0.28033in;height:0.28033in" /><img src="./5caamnk0.png"
style="width:0.282in;height:0.28033in" /><img src="./bfmu4xqy.png"
style="width:0.28033in;height:0.28033in" /><img src="./w3v2sqrv.png"
style="width:0.28033in;height:0.28033in" /><img src="./ue0klycr.png"
style="width:0.28033in;height:0.28033in" /><img src="./bhmpc5zd.png"
style="width:0.28033in;height:0.28033in" /><img src="./kh2qrwuy.png"
style="width:0.282in;height:0.28033in" /><img src="./bycdzx0a.png"
style="width:0.28033in;height:0.28033in" /><img src="./gfv1oloh.png" style="width:0.282in;height:0.282in" /><img src="./dpy2rpgf.png"
style="width:0.282in;height:0.28033in" /><img src="./rbtqvvou.png"
style="width:0.28033in;height:0.28033in" /><img src="./wmtedlrb.png"
style="width:0.28033in;height:0.28033in" /><img src="./1xtq5zxd.png"
style="width:0.28033in;height:0.282in" /><img src="./lks05yhm.png" style="width:0.282in;height:0.282in" /><img src="./yneqacjc.png"
style="width:0.28033in;height:0.282in" /><img src="./mqnvmzio.png" style="width:0.282in;height:0.282in" /><img src="./ngrj5tg1.png"
style="width:0.28033in;height:0.282in" /><img src="./5e2jectz.png"
style="width:0.28033in;height:0.28033in" /><img src="./trk4ulen.png"
style="width:0.282in;height:0.28033in" /><img src="./qpiz1kai.png"
style="width:0.28033in;height:0.28033in" /><img src="./zxn32jrm.png"
style="width:0.28033in;height:0.28033in" /><img src="./mqscwvo3.png"
style="width:0.282in;height:0.28033in" /><img src="./xgvbp2l0.png"
style="width:0.28033in;height:0.28033in" /><img src="./b1byh0vn.png"
style="width:0.282in;height:0.28033in" /><img src="./tbm0k44e.png"
style="width:0.28033in;height:0.28033in" /><img src="./055b0z1p.png"
style="width:0.282in;height:0.28033in" /><img src="./dnprlnrh.png"
style="width:0.28033in;height:0.28033in" /><img src="./gz1pnvld.png"
style="width:0.28033in;height:0.28033in" /><img src="./txgy2xxu.png"
style="width:0.282in;height:0.28033in" /><img src="./nfixjojt.png"
style="width:0.28033in;height:0.28033in" /><img src="./200naale.png"
style="width:0.28033in;height:0.28033in" /><img src="./irge0dml.png"
style="width:0.282in;height:0.28033in" /><img src="./0xtepqty.png"
style="width:0.28033in;height:0.28033in" /><img src="./ev5tjcol.png"
style="width:0.282in;height:0.28033in" /><img src="./jj3bfu5l.png"
style="width:0.28033in;height:0.28033in" /><img src="./hixgaybv.png"
style="width:0.282in;height:0.28033in" /><img src="./3qwslqqv.png"
style="width:0.28033in;height:0.28033in" /><img src="./kuennw4s.png"
style="width:0.282in;height:0.28033in" /><img src="./txmrld3t.png"
style="width:0.28033in;height:0.28033in" /><img src="./uoulajsb.png"
style="width:0.28033in;height:0.28033in" /><img src="./n4dfkdr5.png"
style="width:0.28033in;height:0.282in" /><img src="./kq0foryo.png"
style="width:0.28033in;height:0.282in" /><img src="./sow3a4vy.png"
style="width:0.282in;height:0.28033in" /><img src="./bypwynvs.png"
style="width:0.28033in;height:0.28033in" /><img src="./ax11ehqx.png"
style="width:0.28033in;height:0.28033in" /><img src="./w31hlik5.png"
style="width:0.282in;height:0.28033in" /><img src="./3yq4m4lm.png"
style="width:0.28033in;height:0.28033in" /><img src="./yp50wbx2.png"
style="width:0.28033in;height:0.28033in" /><img src="./x5huk4us.png"
style="width:0.28033in;height:0.28033in" /><img src="./efcvcx00.png"
style="width:0.28033in;height:0.28033in" /><img src="./cbvumn1r.png"
style="width:0.282in;height:0.28033in" /><img src="./xon3td0k.png"
style="width:0.28033in;height:0.28033in" /><img src="./20p4yrli.png"
style="width:0.282in;height:0.28033in" /><img src="./h0b3a0kh.png"
style="width:0.28033in;height:0.28033in" /><img src="./g3uknety.png"
style="width:0.28033in;height:0.28033in" /><img src="./tiwpkuqe.png" style="width:0.282in;height:0.282in" /><img src="./ywrdx4u0.png"
style="width:0.28033in;height:0.282in" /><img src="./uax14er1.png"
style="width:0.28033in;height:0.282in" /><img src="./hfgcdzo1.png"
style="width:0.28033in;height:0.282in" /><img src="./0jmovwcy.png"
style="width:0.28033in;height:0.282in" /><img src="./qhauh31j.png" style="width:0.282in;height:0.282in" /><img src="./ycl2qej2.png"
style="width:0.28033in;height:0.282in" /><img src="./ad4tgv0q.png" style="width:0.282in;height:0.282in" /><img src="./a2421cwi.png"
style="width:0.28033in;height:0.282in" /><img src="./30nmm3js.png"
style="width:0.28033in;height:0.282in" /><img src="./d2qwaclx.png"
style="width:0.282in;height:0.28033in" /><img src="./v4dgewt0.png"
style="width:0.28033in;height:0.28033in" /><img src="./lhtuj0rr.png"
style="width:0.28033in;height:0.28033in" /><img src="./1esqacko.png"
style="width:0.28033in;height:0.28033in" /><img src="./u0zksipq.png"
style="width:0.28033in;height:0.28033in" /><img src="./l4zjt5eh.png"
style="width:0.282in;height:0.28033in" /><img src="./djbp4nyz.png"
style="width:0.28033in;height:0.28033in" /><img src="./pmkqyfsu.png"
style="width:0.282in;height:0.28033in" /><img src="./gn4l5mwc.png"
style="width:0.28033in;height:0.28033in" /><img src="./iu4qj2uo.png"
style="width:0.28033in;height:0.28033in" /><img src="./3hj5gszh.png"
style="width:0.282in;height:0.28033in" /><img src="./ku02tiva.png"
style="width:0.28033in;height:0.28033in" /><img src="./mmwlueif.png"
style="width:0.28033in;height:0.28033in" /><img src="./im4qcaam.png"
style="width:0.28033in;height:0.28033in" /><img src="./14lkk3jf.png"
style="width:0.28033in;height:0.28033in" /><img src="./mvckkru5.png"
style="width:0.282in;height:0.28033in" /><img src="./ffaxfsoi.png"
style="width:0.28033in;height:0.28033in" /><img src="./tuins0wm.png"
style="width:0.282in;height:0.28033in" /><img src="./gmjtuppu.png"
style="width:0.28033in;height:0.28033in" /><img src="./dofk1aem.png"
style="width:0.28033in;height:0.28033in" /><img src="./dijgfdqv.png"
style="width:0.28033in;height:0.28033in" /><img src="./h3sgtowb.png"
style="width:0.282in;height:0.28033in" /><img src="./uyy4wq24.png"
style="width:0.28033in;height:0.282in" /><img src="./bnyfbnzq.png" style="width:0.282in;height:0.282in" /><img src="./3zwuxhjc.png"
style="width:0.28033in;height:0.282in" /><img src="./0ecn2hvw.png" style="width:0.282in;height:0.282in" /><img src="./kegq4eo3.png" style="height:0.16406in" /><img src="./ucmb5qyn.png" style="height:0.10677in" /><img src="./2we55tde.png" style="height:0.19618in" /><img src="./44ryi2sd.png" style="height:0.1059in" /><img src="./f3sntivl.png" style="height:0.19705in" /><img src="./5uo1bbns.png" style="height:0.16406in" /><img src="./uhqf1xys.png" style="height:0.1059in" />

<img src="./g54xqzsp.png"
style="width:0.282in;height:0.28033in" /><img src="./nabmtahr.png"
style="width:0.28033in;height:0.28033in" /><img src="./srywpo3d.png"
style="width:0.28033in;height:0.28033in" />Fig. 5. Recovered input in
query-free attacks.

> <img src="./tsfkf2w5.png"
> style="width:0.28033in;height:0.28033in" /><img src="./sbric1m0.png"
> style="width:0.282in;height:0.28033in" /><img src="./2az2ntb5.png"
> style="width:0.28033in;height:0.28033in" /><img src="./clr30vng.png"
> style="width:0.28033in;height:0.28033in" /><img src="./dq4px31k.png"
> style="width:0.282in;height:0.28033in" /><img src="./imspjkoq.png"
> style="width:0.28033in;height:0.28033in" /><img src="./j04bdvvp.png"
> style="width:0.282in;height:0.28033in" /><img src="./ssnaseq0.png"
> style="width:0.28033in;height:0.28033in" /><img src="./efl3lgaj.png"
> style="width:0.282in;height:0.28033in" /><img src="./rquje0ma.png"
> style="width:0.28033in;height:0.28033in" /><img src="./ylexkfle.png"
> style="width:0.28033in;height:0.282in" /><img src="./ogngne44.png" style="width:0.282in;height:0.282in" /><img src="./mcu50uwy.png"
> style="width:0.28033in;height:0.282in" /><img src="./e4wes2r1.png"
> style="width:0.28033in;height:0.282in" /><img src="./novctyb5.png" style="width:0.282in;height:0.282in" /><img src="./vl3h5mkw.png"
> style="width:0.28033in;height:0.282in" /><img src="./j4kcvodg.png" style="width:0.282in;height:0.282in" /><img src="./n5a2kbqj.png"
> style="width:0.28033in;height:0.282in" /><img src="./lwgp33ef.png" style="width:0.282in;height:0.282in" /><img src="./hrskfmdh.png"
> style="width:0.28033in;height:0.282in" />Fig. 7. Examples of adding
> the Laplacian noise to defend against a white-box attack on (a) MNIST
> (ReLU2) and (b) CIFAR10 (ReLU22). *b* is the standard deviation of the
> Laplacian noise.

<img src="./0mo32ywn.png"
style="width:0.28033in;height:0.28033in" /><img src="./1r40qm4p.png"
style="width:0.282in;height:0.28033in" /><img src="./0zdivmt3.png"
style="width:0.28033in;height:0.28033in" /><img src="./h2fdnxqy.png"
style="width:0.282in;height:0.28033in" /><img src="./pd1pgjfw.png"
style="width:0.28033in;height:0.28033in" /><img src="./ufiuhrio.png"
style="width:0.282in;height:0.28033in" />Fig. 6. Examples of adding the
Gaussian noise to defend against a white-box attack on (a) MNIST (ReLU2)
and (b) CIFAR10 (ReLU22). *σ* is the standard deviation of the Gaussian
noise.

<img src="./pfef04ye.png"
style="width:0.282in;height:0.28033in" /><img src="./ibcbkwlt.png"
style="width:0.28033in;height:0.28033in" /><img src="./zrf2wgeo.png"
style="width:0.282in;height:0.28033in" /><img src="./gw4gbnsd.png"
style="width:0.28033in;height:0.28033in" /><img src="./iyrs0kly.png"
style="width:0.282in;height:0.28033in" /><img src="./rfwhf3nb.png"
style="width:0.28033in;height:0.28033in" /><img src="./n0tny2x1.png"
style="width:0.28033in;height:0.28033in" /><img src="./v4pyn1lm.png"
style="width:0.282in;height:0.28033in" /><img src="./faqlmmsa.png"
style="width:0.28033in;height:0.28033in" /><img src="./30pcmxzs.png"
style="width:0.282in;height:0.28033in" /><img src="./dc1qntdk.png" style="width:0.282in;height:0.282in" /><img src="./so5aha3v.png"
style="width:0.28033in;height:0.282in" /><img src="./hb22sbab.png" style="width:0.282in;height:0.282in" /><img src="./ij3kemef.png"
style="width:0.28033in;height:0.282in" /><img src="./u3e3c4ry.png" style="width:0.282in;height:0.282in" /><img src="./2u5uhmhy.png"
style="width:0.28033in;height:0.282in" /><img src="./qyjcahps.png"
style="width:0.28033in;height:0.282in" /><img src="./i5jsjwgt.png" style="width:0.282in;height:0.282in" /><img src="./q2vizpjy.png"
style="width:0.28033in;height:0.282in" /><img src="./vcawvzxu.png" style="width:0.282in;height:0.282in" /><img src="./nowq4jf2.png"
style="width:0.282in;height:0.28033in" /><img src="./4keglsj1.png"
style="width:0.28033in;height:0.28033in" /><img src="./rx0umjgb.png"
style="width:0.282in;height:0.28033in" /><img src="./fhmvvewl.png"
style="width:0.28033in;height:0.28033in" /><img src="./pgclwnkt.png"
style="width:0.282in;height:0.28033in" /><img src="./eu0525ug.png"
style="width:0.28033in;height:0.28033in" /><img src="./mhs2dhlj.png"
style="width:0.28033in;height:0.28033in" /><img src="./agjg01vx.png"
style="width:0.282in;height:0.28033in" /><img src="./lu1tthhm.png"
style="width:0.28033in;height:0.28033in" /><img src="./psuo5qvr.png"
style="width:0.282in;height:0.28033in" /><img src="./j0345czq.png"
style="width:0.282in;height:0.28033in" /><img src="./rk4tz4sc.png"
style="width:0.28033in;height:0.28033in" /><img src="./hjdlmo1r.png"
style="width:0.282in;height:0.28033in" /><img src="./zmyqva0d.png"
style="width:0.28033in;height:0.28033in" /><img src="./t1vedkez.png"
style="width:0.282in;height:0.28033in" /><img src="./cmzlucbo.png"
style="width:0.28033in;height:0.28033in" /><img src="./exrkrczq.png"
style="width:0.28033in;height:0.28033in" /><img src="./5iqr21tl.png"
style="width:0.282in;height:0.28033in" /><img src="./lp0pyfck.png"
style="width:0.28033in;height:0.28033in" /><img src="./zevbxnug.png"
style="width:0.282in;height:0.28033in" /><img src="./nibdjt0q.png" style="height:0.19705in" />method
proposed in past work (though it did not speciﬁcally target the
edge–cloud privacy attacks), *viz*., noise obfuscation. We show its
ineffectiveness in defeating our inference data privacy attacks. Then,
we introduce two new strategies that can better prevent privacy leakage
with a small impact on the system’s performance and functionalities.

*A.* *Obfuscation* *With* *Random* *Noise*

Differential privacy has been proposed to protect model inference
\[22\], \[23\] through adding random noise to the input. In the
edge–cloud scenario, we can either add noise to the original input: *v*
= *fθ*1*(x* + *)*, or add noise directly to the intermediate value
before sending it to the untrusted cloud C : *v* = *fθ*1*(x)* + . There
is a tradeoff between usability and privacy: as a higher level of noise
is added, the model accuracy will drop. Whether this tradeoff can be
balanced is critical for the effectiveness of this approach. Below, we
mea-sure the attack effects as well as the model accuracy using noise
obfuscation.

We consider the Gaussian and Laplacian noise in our experiments. Figs.
6(a) and (b) (Gaussian) and 7(a) and (b) (Laplacian) visually show the
recovered images on the MNIST and CIFAR10 data sets, when we add
different levels of noise to the input (ﬁrst two rows in each ﬁgure) or
the intermediate layer output (last two rows). We observe that adding
enough

Fig. 8. Examples of dropout to defend against a white-box attack on (a)
MNIST (ReLU2) and (b) CIFAR10 (ReLU22). *r* is the dropout ratio.

noise can indeed provide better privacy and decrease the qual-ity of
recovered images. Besides, noise at the original input is more effective
than noise at the intermediate layer.

We provide a quantitative analysis of model accuracy (usability,
*y*-axis) and inversed image quality (privacy, *x*-axis) in Figs. 9 and
10 on MNIST and CIFAR10 data sets, respec-tively. The Gaussian and
Laplacian noise are represented as blue and orange lines, respectively.
Adding noise to the input and the intermediate layer are represented as
solid and dotted lines, respectively. The top-left region of the graph
is the best. When ﬁxing the recovered image quality (SSIM or PSNR), the
model accuracy drops more if the noise is added to the input (blue and
orange solid lines) than to the intermediate

> Authorized licensed use limited to: Universiteit van Amsterdam.
> Downloaded on May 19,2026 at 12:04:50 UTC from IEEE Xplore.
> Restrictions apply.

9712 IEEE INTERNET OF THINGS JOURNAL, VOL. 8, NO. 12, JUNE 15,
2021<img src="./qkt3zopa.png" style="width:1.27028in" /><img src="./wh1nc1xs.png" style="width:0.47049in" /><img src="./444fuzgm.png"
style="width:0.24276in;height:0.32986in" /><img src="./sdtgf3un.png" style="width:0.15278in" /><img src="./j03ey5ct.png"
style="width:0.22917in;height:0.17622in" /><img src="./ckhcwypa.png" style="height:0.35764in" /><img src="./tynffhdu.png" style="width:0.93663in" /><img src="./ji32cavj.png"
style="width:2.77493in;height:1.51164in" /><img src="./rwfqisv2.png"
style="width:0.61842in;height:0.60156in" /><img src="./tiocyadp.png" style="height:0.10243in" /><img src="./ukbgn234.png" style="width:0.35683in" /><img src="./1qfycfsj.png" style="width:0.17014in" /><img src="./xkjercw2.png" style="width:0.15255in" /><img src="./s2br15r2.png" style="height:0.35851in" /><img src="./ng1frjdh.png" style="width:1.2706in" /><img src="./4gcdx2vh.png" style="width:0.15972in" />

<img src="./jwmfi0ng.png"
style="width:2.67724in;height:1.51388in" /><img src="./vymuqpor.png"
style="width:0.24276in;height:0.2092in" /><img src="./3musms0v.png"
style="width:0.79617in;height:0.79167in" /><img src="./hw3xly3g.png"
style="width:0.1467in;height:0.10243in" /><img src="./e35sxcvv.png" style="width:0.15491in" /><img src="./xdr2a2x0.png" style="width:0.17448in" /><img src="./nqidjzxm.png" style="height:0.35851in" />layer
(blue and orange dotted lines). This is consistent with the visual
observations in Figs. 6(c) and 7(c). Different charac-teristics of noise
distributions, e.g., the Gaussian or Laplacian, do not show a signiﬁcant
difference in model accuracy.

<img src="./mmi0w4r0.png" style="width:0.93663in" /><img src="./tbn3sptv.png"
style="width:2.75918in;height:1.51164in" /><img src="./cqugml5f.png" style="width:0.18736in" /><img src="./01qzf44y.png"
style="width:0.12413in;height:0.20312in" /><img src="./31mekh0o.png"
style="width:0.14757in;height:0.10243in" /><img src="./im3pglcn.png"
style="width:0.15405in;height:0.10156in" /><img src="./l1kkhv3n.png" style="height:0.35851in" />On
the MNIST data set (Fig. 9), to maintain a good model accuracy (i.e.,
*\>*95%), the noise level must be restricted to *σ* *\<* 0*.*8 and *b*
*\<* 0*.*5*.* At this level, the attacker is still able to recover
images with high quality (SSIM *\>* 0.4 and PSNR *\>* 8.5 dB). Similar
results are shown on the CIFAR10 data set in Fig. 10. While recent work
\[6\], \[13\] proposed spe-cial algorithms for designing noise to
protect inference data privacy, they still may not work for our new
attacks or need extra special training of the noise generator. Hence, we
pro-pose new defense methods below that are not based on adding noise
and are more practical in that they protect the inference data privacy
with much smaller performance degradation.

*B.* *Dropout* *Defense*

Since noise obfuscation may not be secure, we propose another
randomization-based solution, dropout, to defeat the proposed attacks.
Dropout deactivates random neurons in one layer by setting their output
to 0. Formally, it calculates

> *fi*dropout*(x)* = *f(x)*⊗*M* (6)

where *M* is a mask, where each element of *M* is randomly assigned a
value of 0 with probability *r* and a value of 1 with probability 1−*r*.
⊗ denotes the elementwise multiplica-tion. Intuitively, dropout
leverages the redundancy feature of neural networks \[24\], such that
removing partial information in the inference does not degrade the model
performance but obfuscates the input data.

Similar to noise obfuscation, dropout can also be applied to the input
or the intermediate layer output. We show exam-ples of the images
recovered from layer ReLU2 (MNIST) in Fig. 8(c). The top two rows
represent the effect of dropout on input, while the bottom two rows
represent that on intermediate output. We observe that increasing the
dropout rate *r* decreases the quality of inversed images. No useful
information can be obtained by the attacker when *r* reaches 0.6. We
show reversed images from ReLU22 (CIFAR10) in Fig. 8(b). Similarly, no
useful information can be obtained when *r* reaches 0.6.

We further measure the usability–privacy tradeoff of dropout and compare
it with the noise obfuscation approach (Fig. 9 on MNIST and Fig. 10 on
CIFAR10). Higher accuracy repre-sents better usability, while smaller
SSIM and PSNR represent better privacy. Lines that are closer to the
top-left region have a better tradeoff. We observe that dropout (green
lines) signiﬁcantly outperforms all the noise obfuscation solutions
(blue and orange lines). This is because dropout leverages DNN model
redundancy to hide partial information and main-tain model accuracy
while adding random noise introduces obfuscation on all neurons which
degrade model accuracy. Besides, dropout on the intermediate layer
(green dotted line) is slightly better than dropout on the input (green
solid line): it can fully protect the inference data privacy (SSIM *\<*
0.25) with accuracy *\>* 95%. On the CIFAR10 data

Fig. 9. Model accuracy versus the SSIM (top) and PSNR (bottom) of
inversed images on the MNIST data set.

Fig. 10. Model accuracy versus the SSIM (top) and PSNR (bottom) of
inversed images on the CIFAR10 data set.

set, dropout on the intermediate layer signiﬁcantly overper-forms the
other approaches, fully protecting inference data privacy (SSIM *\<*
0.25) with *\<*0.8% drop in accuracy.

To fully evaluate the effectiveness of this dropout mecha-nism, we
consider splitting the model at different layers on the MNIST data set.
We conduct dropout on the intermediate layer (i.e., the split layer)
since it is better than that on the input.

> Authorized licensed use limited to: Universiteit van Amsterdam.
> Downloaded on May 19,2026 at 12:04:50 UTC from IEEE Xplore.
> Restrictions apply.

HE *et* *al.*: ATTACKING AND PROTECTING DATA PRIVACY IN EDGE–CLOUD
COLLABORATIVE INFERENCE SYSTEMS 9713<img src="./t4csphsb.png"
style="width:0.28033in;height:0.282in" /><img src="./ubmnpruv.png"
style="width:0.28033in;height:0.282in" /><img src="./3j01fk2a.png"
style="width:0.28033in;height:0.282in" /><img src="./l1wu53xp.png" style="width:0.282in;height:0.282in" /><img src="./0vrqfxdo.png"
style="width:0.28033in;height:0.282in" /><img src="./adlkx4ps.png" style="width:0.282in;height:0.282in" /><img src="./ohuk1vww.png"
style="width:0.28033in;height:0.282in" /><img src="./xizailv5.png" style="width:0.282in;height:0.282in" /><img src="./nhxlbdgw.png"
style="width:0.28033in;height:0.282in" /><img src="./ahpqk0lp.png"
style="width:0.28033in;height:0.28033in" /><img src="./mwaj0hvf.png"
style="width:0.28033in;height:0.28033in" /><img src="./y5r4goze.png"
style="width:0.28033in;height:0.28033in" /><img src="./n3oewal2.png"
style="width:0.28033in;height:0.28033in" /><img src="./sl25bco5.png"
style="width:0.282in;height:0.28033in" /><img src="./1cuwrobb.png"
style="width:0.28033in;height:0.28033in" /><img src="./3m4lxkvq.png"
style="width:0.282in;height:0.28033in" /><img src="./xsob5iwg.png"
style="width:0.28033in;height:0.28033in" /><img src="./f0wrjwds.png"
style="width:0.282in;height:0.28033in" /><img src="./gnx2erwc.png"
style="width:0.28033in;height:0.28033in" /><img src="./hprhdcdx.png"
style="width:0.28033in;height:0.28033in" /><img src="./pvucqgeo.png"
style="width:0.28033in;height:0.28033in" /><img src="./ulxvvzis.png"
style="width:0.282in;height:0.28033in" /><img src="./xpj1ip0j.png"
style="width:0.28033in;height:0.28033in" /><img src="./4zfdz0r3.png" style="width:0.282in;height:0.282in" /><img src="./qevxsdu5.png" style="width:0.282in;height:0.282in" /><img src="./fsobkij3.png"
style="width:0.28033in;height:0.282in" /><img src="./2gt0byxu.png"
style="width:0.28033in;height:0.282in" /><img src="./cgybjsw3.png"
style="width:0.28033in;height:0.282in" /><img src="./hywzstb5.png"
style="width:0.28033in;height:0.282in" /><img src="./llwjm4jc.png"
style="width:0.28033in;height:0.282in" /><img src="./5sdqnlms.png" style="width:0.282in;height:0.282in" /><img src="./fuvafahf.png"
style="width:0.28033in;height:0.282in" /><img src="./sbqyfl4e.png" style="width:0.282in;height:0.282in" /><img src="./abc4ja5o.png"
style="width:0.28033in;height:0.282in" /><img src="./e4uayzkb.png"
style="width:0.28033in;height:0.282in" /><img src="./anu5qwiw.png"
style="width:0.28033in;height:0.282in" /><img src="./thesegu3.png"
style="width:0.28033in;height:0.28033in" /><img src="./anxzk2pq.png"
style="width:0.28033in;height:0.28033in" /><img src="./2iglqrlp.png"
style="width:0.28033in;height:0.28033in" /><img src="./agggxhal.png"
style="width:0.28033in;height:0.28033in" /><img src="./fkajhmuw.png"
style="width:0.282in;height:0.28033in" /><img src="./omoxhcz0.png"
style="width:0.28033in;height:0.28033in" /><img src="./jj4rrw0q.png"
style="width:0.282in;height:0.28033in" /><img src="./ctnkihqd.png"
style="width:0.28033in;height:0.28033in" /><img src="./z2upi5iq.png"
style="width:0.28033in;height:0.28033in" /><img src="./5efatg0z.png"
style="width:0.28033in;height:0.28033in" /><img src="./bjk051jx.png"
style="width:0.28033in;height:0.28033in" /><img src="./p1fsgvis.png"
style="width:0.28033in;height:0.28033in" /><img src="./ctw3ngwe.png"
style="width:0.28033in;height:0.28033in" /><img src="./afidf0jz.png"
style="width:0.28033in;height:0.28033in" /><img src="./cqz2mj1a.png"
style="width:0.282in;height:0.28033in" /><img src="./cg0ojju3.png"
style="width:0.28033in;height:0.28033in" /><img src="./jcn0uss2.png"
style="width:0.282in;height:0.28033in" /><img src="./sikgbl4o.png"
style="width:0.28033in;height:0.28033in" /><img src="./cebxqtlv.png"
style="width:0.28033in;height:0.28033in" /><img src="./h0egwubl.png"
style="width:0.28033in;height:0.28033in" /><img src="./kupoff4v.png"
style="width:0.28033in;height:0.282in" /><img src="./li4fg2xv.png"
style="width:0.28033in;height:0.282in" /><img src="./hpcz4kjh.png"
style="width:0.28033in;height:0.282in" /><img src="./0k35a0zk.png"
style="width:0.28033in;height:0.282in" /><img src="./lrfuitlh.png" style="width:0.282in;height:0.282in" /><img src="./ngmmdwdx.png"
style="width:0.28033in;height:0.282in" /><img src="./2uimazpp.png" style="width:0.282in;height:0.282in" /><img src="./0vnjahkg.png"
style="width:0.28033in;height:0.282in" /><img src="./xtx43asi.png"
style="width:0.28033in;height:0.282in" /><img src="./l3mifsa2.png"
style="width:0.28033in;height:0.282in" /><img src="./mt5inyxl.png"
style="width:0.28033in;height:0.282in" /><img src="./m2ef000w.png"
style="width:0.28033in;height:0.282in" /><img src="./xgfktocu.png"
style="width:0.28033in;height:0.282in" /><img src="./r2xjltcn.png"
style="width:0.28033in;height:0.282in" /><img src="./jkuszofj.png" style="width:0.282in;height:0.282in" /><img src="./zeznq4cx.png"
style="width:0.28033in;height:0.282in" /><img src="./bcjgva2r.png" style="width:0.282in;height:0.282in" /><img src="./e3ginrc0.png"
style="width:0.28033in;height:0.282in" /><img src="./o2nrmv42.png"
style="width:0.28033in;height:0.282in" /><img src="./bs1tslv3.png"
style="width:0.28033in;height:0.282in" /><img src="./5zxl55st.png"
style="width:0.28033in;height:0.28033in" /><img src="./vezdr0jf.png"
style="width:0.282in;height:0.28033in" /><img src="./wu52eeuj.png"
style="width:0.28033in;height:0.28033in" /><img src="./nwkqvq3x.png"
style="width:0.28033in;height:0.28033in" /><img src="./zrr2oknl.png"
style="width:0.282in;height:0.28033in" /><img src="./grnnzepo.png"
style="width:0.28033in;height:0.28033in" /><img src="./0gooy4k4.png"
style="width:0.282in;height:0.28033in" /><img src="./s55y1rtd.png"
style="width:0.28033in;height:0.28033in" /><img src="./5u4fxcpk.png"
style="width:0.282in;height:0.28033in" /><img src="./z5rqe4sl.png"
style="width:0.28033in;height:0.28033in" /><img src="./k1vob4as.png"
style="width:0.28033in;height:0.282in" /><img src="./l3fvibhj.png" style="width:0.282in;height:0.282in" /><img src="./p4axq3z0.png"
style="width:0.28033in;height:0.282in" /><img src="./x5twhhnv.png"
style="width:0.28033in;height:0.282in" /><img src="./nxnbf1rm.png" style="width:0.282in;height:0.282in" /><img src="./xn0odpvy.png"
style="width:0.28033in;height:0.282in" /><img src="./mesyvlci.png" style="width:0.282in;height:0.282in" /><img src="./yg5dsbxf.png"
style="width:0.28033in;height:0.282in" /><img src="./itp3otho.png" style="width:0.282in;height:0.282in" /><img src="./yyjlc1ev.png"
style="width:0.28033in;height:0.282in" /><img src="./ecm1gy3u.png"
style="width:0.28033in;height:0.282in" /><img src="./wwroobis.png" style="width:0.282in;height:0.282in" /><img src="./ivjdeamc.png"
style="width:0.28033in;height:0.282in" /><img src="./c0tpg5io.png"
style="width:0.28033in;height:0.282in" /><img src="./jia505a3.png" style="width:0.282in;height:0.282in" /><img src="./hu0oa2j0.png"
style="width:0.28033in;height:0.282in" /><img src="./skhdnf0u.png" style="width:0.282in;height:0.282in" /><img src="./gv1exmti.png"
style="width:0.28033in;height:0.282in" /><img src="./jvrz431s.png" style="width:0.282in;height:0.282in" /><img src="./mexhirky.png"
style="width:0.28033in;height:0.282in" /><img src="./lkq1ldy1.png"
style="width:0.28033in;height:0.28033in" /><img src="./312avo5j.png"
style="width:0.28033in;height:0.28033in" /><img src="./ia40tuwt.png"
style="width:0.282in;height:0.28033in" /><img src="./qlbsy3cj.png"
style="width:0.28033in;height:0.28033in" /><img src="./5u1lk5cf.png"
style="width:0.28033in;height:0.28033in" /><img src="./scwyyv5b.png"
style="width:0.28033in;height:0.28033in" /><img src="./z5ilg3wg.png"
style="width:0.28033in;height:0.28033in" /><img src="./d4egvbuy.png"
style="width:0.282in;height:0.28033in" /><img src="./55o2x2w3.png"
style="width:0.28033in;height:0.28033in" /><img src="./01agluzz.png"
style="width:0.282in;height:0.28033in" /><img src="./np3ehaps.png"
style="width:0.28033in;height:0.28033in" /><img src="./fys4mi21.png"
style="width:0.28033in;height:0.282in" /><img src="./5b0b3zgd.png" style="width:0.282in;height:0.282in" /><img src="./10twojyv.png"
style="width:0.28033in;height:0.282in" /><img src="./yvo5sfrd.png"
style="width:0.28033in;height:0.282in" /><img src="./xmvpwo2j.png" style="width:0.282in;height:0.282in" /><img src="./4oxvl4h5.png"
style="width:0.28033in;height:0.282in" /><img src="./xvvs1ovq.png" style="width:0.282in;height:0.282in" /><img src="./w2w151b4.png"
style="width:0.28033in;height:0.282in" /><img src="./1u3pnz50.png" style="width:0.282in;height:0.282in" /><img src="./gil1tziq.png"
style="width:0.28033in;height:0.282in" /><img src="./kr20m4jh.png"
style="width:1.46097in;height:1.06399in" /><img src="./kdmjtfl4.png"
style="width:0.14062in;height:0.33507in" /><img src="./r0r0jeii.png"
style="width:1.4613in;height:1.05946in" /><img src="./jq1cqm24.png"
style="width:0.14149in;height:0.33507in" /><img src="./sxxvgbkn.png"
style="width:0.17882in;height:0.1875in" /><img src="./uic11qeh.png"
style="width:0.23437in;height:0.22917in" /><img src="./hujdrbob.png"
style="width:0.17795in;height:0.19885in" /><img src="./vciid01j.png"
style="width:0.17795in;height:0.18576in" /><img src="./sayr4txh.png"
style="width:0.23351in;height:0.22743in" /><img src="./h5ocefem.png"
style="width:0.17708in;height:0.19812in" /><img src="./evyofhif.png"
style="width:0.11198in;height:0.11545in" /><img src="./3khytq0u.png"
style="width:0.19444in;height:0.20052in" /><img src="./o5mlwp1v.png"
style="width:0.11111in;height:0.11458in" /><img src="./afpfdmoz.png"
style="width:0.19531in;height:0.20052in" /><img src="./42ok21yb.png"
style="width:0.10415in;height:0.11545in" /><img src="./ws50pl5j.png" style="width:0.30035in" /><img src="./gne0u4nl.png" style="width:0.27778in" />

> <img src="./xbeuuwb5.png"
> style="width:0.28033in;height:0.282in" />Fig. 13. Model accuracy
> versus the SSIM (left) and PSNR (right) of inversed image.

<img src="./aq5kjdmc.png"
style="width:0.28033in;height:0.282in" /><img src="./d1tr5ycd.png" style="width:0.282in;height:0.282in" /><img src="./cslzubk0.png"
style="width:0.28033in;height:0.282in" /><img src="./dn3u4pna.png"
style="width:0.28033in;height:0.282in" /><img src="./oaz3nb5o.png" style="width:0.282in;height:0.282in" /><img src="./oiapvfey.png"
style="width:0.28033in;height:0.282in" /><img src="./i2tbpbwx.png" style="width:0.282in;height:0.282in" /><img src="./ik2fkana.png"
style="width:0.28033in;height:0.282in" /><img src="./mlji4cgl.png" style="width:0.282in;height:0.282in" /><img src="./rmdqtxhr.png"
style="width:0.28033in;height:0.282in" /><img src="./vxqntx0n.png"
style="width:0.28033in;height:0.28033in" /><img src="./y1ympi0c.png"
style="width:0.282in;height:0.28033in" /><img src="./uyyxk4dz.png"
style="width:0.28033in;height:0.28033in" /><img src="./l14bcbjj.png"
style="width:0.28033in;height:0.28033in" /><img src="./n3a0gce4.png"
style="width:0.282in;height:0.28033in" /><img src="./vteotsqn.png"
style="width:0.28033in;height:0.28033in" /><img src="./jqyoolps.png"
style="width:0.282in;height:0.28033in" /><img src="./sb4wagaa.png"
style="width:0.28033in;height:0.28033in" /><img src="./v2bmk5ph.png"
style="width:0.282in;height:0.28033in" /><img src="./q3ltjgmg.png"
style="width:0.28033in;height:0.28033in" />Fig. 11. Dropout as a defense
against attacks at different layers on the MNIST data set. Rows from top
to bottom: ReLU1, pool1, conv2, ReLU2, and pool2.

<img src="./tqtlruf4.png"
style="width:0.28033in;height:0.282in" /><img src="./hort3vsx.png" style="width:0.282in;height:0.282in" /><img src="./dxmlohye.png"
style="width:0.28033in;height:0.282in" /><img src="./go2hnzw1.png"
style="width:0.28033in;height:0.282in" /><img src="./j2qznree.png" style="width:0.282in;height:0.282in" /><img src="./qk55h4em.png"
style="width:0.28033in;height:0.282in" /><img src="./amz5h2qw.png" style="width:0.282in;height:0.282in" /><img src="./j5vbqn4o.png"
style="width:0.28033in;height:0.282in" /><img src="./wonhfqxq.png" style="width:0.282in;height:0.282in" /><img src="./hxzdwkbx.png"
style="width:0.28033in;height:0.282in" /><img src="./x2itoau5.png"
style="width:0.28033in;height:0.28033in" /><img src="./gxendgna.png"
style="width:0.282in;height:0.28033in" /><img src="./cgdy55mw.png"
style="width:0.28033in;height:0.28033in" /><img src="./rsa3ljrz.png"
style="width:0.28033in;height:0.28033in" /><img src="./va0bxqnz.png"
style="width:0.282in;height:0.28033in" /><img src="./23ab5o0k.png"
style="width:0.28033in;height:0.28033in" /><img src="./sat5m1w0.png"
style="width:0.282in;height:0.28033in" /><img src="./sfzeei4a.png"
style="width:0.28033in;height:0.28033in" /><img src="./vf05cq0q.png"
style="width:0.282in;height:0.28033in" /><img src="./2qbt5dwq.png"
style="width:0.28033in;height:0.28033in" /><img src="./22anyngb.png"
style="width:0.28033in;height:0.28033in" /><img src="./cqjxte2k.png"
style="width:0.282in;height:0.28033in" /><img src="./j4gg1bfe.png"
style="width:0.28033in;height:0.28033in" /><img src="./ceq5yavr.png"
style="width:0.28033in;height:0.28033in" /><img src="./mfubol0q.png"
style="width:0.282in;height:0.28033in" /><img src="./djgodfqf.png"
style="width:0.28033in;height:0.28033in" /><img src="./pfh0xgjv.png"
style="width:0.282in;height:0.28033in" /><img src="./x1z3lxph.png"
style="width:0.28033in;height:0.28033in" /><img src="./cpgnke2y.png"
style="width:0.282in;height:0.28033in" /><img src="./0gfti3e5.png"
style="width:0.28033in;height:0.28033in" />Fig. 12. Dropout as a defense
against attacks at different layers on the CIFAR10 data set. Rows from
top to bottom: ReLU12, pool1, conv22, ReLU22, and pool2.

Fig. 11 shows the recovered images from shallow to deep lay-ers: ReLU1,
pool1, conv2, ReLU2, and pool2. We observe that as the split layer
becomes deeper, a smaller dropout rate is sufﬁcient to prevent privacy
leakage. For example, to fully obfuscate the input, *r* can be set as
0.9 when the model is split at the ReLU1 layer (the ﬁrst row), and 0.2
when the model is split at the pool2 layer (the last row). This can be
better illustrated in the usability–privacy curves in Fig. 13: dropout
on deeper layers is more effective (closer to top-left regions) than
that on shallow layers. For both SSIM and PSNR, we have from worse to
better: pool1(blue), then conv2 (green), then ReLU2 (orange), and then
pool2 (gray). There is only one exception: the ReLU1 layer, which does
better than expected. It is the best for SSIM and better than conv2 for
PSNR. One possible reason is that the recovered image maintains a
visu-ally recognizable structure but degrades illumination in the ReLU1
layer, which contributes more signiﬁcantly to PSNR and SSIM than human
recognition. Similar results on the CIFAR10 data set are shown in Fig.
12.

Fig. 14.

Fig. 15.

Recovered images in query-free attacks.

PSNR and SSIM in query-free attacks.

*C.* *Privacy-Aware* *DNN* *Partitioning*

Section III shows that different split points yield differ-ent attack
effects. This observation leads to another possible defense strategy:
privacy-aware model partitioning. We raise an important question: *how*
*to* *split* *the* *neural* *network* *in* *the* *collaborative*
*system,* *to* *make* *the* *inference* *data* *more* *secure?* We use
the query-free attack as an example to explore this question. We select
the split point at each layer and perform

inference privacy attacks. Figs. 14 and 15 show the recovered images and
PSNR/SSIM metrics, respectively.

Generally, we observe that the quality of recovered images decreases
when the split layer becomes deeper. This is straight-forward as the
relationship between input and output becomes more complicated and
harder to revert when there are more layers. Besides, we also observe
that the image quality drops signiﬁcantly, both qualitatively (Fig. 14)
and quantitatively

> Authorized licensed use limited to: Universiteit van Amsterdam.
> Downloaded on May 19,2026 at 12:04:50 UTC from IEEE Xplore.
> Restrictions apply.

9714

(Fig. 15), on the fully connected layer (fc1), indicating that model
inversion with fully connected layers is much harder than that with
convolutional layers. The reason is that a con-volutional layer only
operates on local elements (the locality depends on the kernel size),
while a fully connected layer entirely mixes up the patterns from the
previous layer. Besides, the number of output neurons in a fully
connected layer is typically much smaller than input neurons. So it is
relatively harder to ﬁnd the reversed relationship from the output of
the fully connected layer to the input.

*Privacy-Aware* *Partitioning* *Strategy:* When selecting the split
point in a collaborative inference system, privacy should also be
considered, in addition to latency and power con-straints. We recommend
placing at least one fully connected layer on the edge device to hide
the information of sensitive input samples.

V. RELATED WORK *A.* *Machine* *Learning* *Privacy* *Attacks*

*Training* *Data* *Privacy* *Attacks:* There are different types of
privacy attacks against the training data. The ﬁrst type is *property*
*inference* *attacks*, which try to infer some properties of the
training data from the model parameters. Attacks were demonstrated in
traditional machine learning classiﬁers \[25\] and fully connected
neural networks \[26\].

A special case of property inference attacks is *membership* *inference*
*attacks*, which infer whether one individual sample is included in the
training set. This attack was ﬁrst presented in \[27\]. The following
work explored the feasibility of attacks with different adversary’s
capabilities \[28\], model fea-tures \[29\], \[30\], in generative
adversarial networks \[31\], \[32\], and collaborative training systems
\[33\].

The second type of attacks against the training data’s privacy are
*model* *inversion* *attacks* \[34\]: given a machine learning model,
and part of the training samples’ features, the adversary can recover
the rest of the features of the samples. Advanced model inversion
attacks were designed to recover images from DNNs in single-party
systems \[35\], and collaborative learning systems \[36\].

The third type is *model* *encoding* *attacks* \[37\]: the adversary
with direct access to the training data can encode the sensitive data
into the model for a receiver entity to retrieve.

*Model* *Privacy* *Attacks:* The adversary attempts to steal the model
parameters \[18\], hyperparameters \[20\], or struc-tures \[19\],
\[38\], via prediction APIs, memory side channels, etc.

*Inference* *Data* *Privacy* *Attacks:* Closer to our study is the work
\[39\], which trains an inverse network on the output prob-ability
distribution to get the inversed inference data. However, they only
consider the model inversion attack from the softmax layer in the
black-box scenario. We show that the attacker can successfully inverse
the model from different layers, even in a stricter query-free scenario.
We also provide defense strategies that are not discussed in their
paper. Wei *et* *al.* \[40\] adopted a power side channel to recover
inference data. However, this attack required the adversary to
compromise the victim device for side-channel information collection,
and it could only

> IEEE INTERNET OF THINGS JOURNAL, VOL. 8, NO. 12, JUNE 15, 2021

recover simple images (single pixel). Our work can recover any arbitrary
complex data without access to, or knowledge of, the victim’s device and
computation.

*B.* *Machine* *Learning* *Privacy* *Solutions*

*Enhancing* *the* *Algorithms:* Distributed training was intro-duced to
protect the training data \[41\], \[42\], as different participants can
use their own data for model training. The SGX security enclaves in
Intel processors were used to protect the training tasks against
privileged adversaries \[43\], \[44\]. Cao and Yang \[45\] proposed a
methodology to remove the effects of sensitive training samples on the
models. Abadi *et* *al.* \[46\] applied differential privacy to add
noise in the SGD process to eliminate the parameters’ dependency on the
training data. *Enhancing* *the* *Training* *Data* *Set:* Bost *et*
*al.* \[47\] proposed to encrypt the data before feeding them into the
training algo-rithm. They designed machine learning operators that can
operate on the encrypted data. Zhang *et* *al.* \[48\] showed that
adding noise to the training data set is effective in protect-ing
training data privacy. Generating artiﬁcial data \[49\]–\[51\] has been
proposed for training DNN models while removing

sensitive information from the original data.

*Obfruscating* *the* *Inference* *Input:* Differential privacy has been
proposed to protect model inference \[22\], \[23\] through adding random
noise to the input. We show that just adding noise cannot defend against
our attacks, and hence we also propose two defenses that may be more
practical for our attacks in this article. Recent work \[6\] proposed to
add spe-cially designed noise and provided a theoretical analysis on the
input data privacy leakage. However, it did not consider the model
inversion attacks that we propose and requires extra training of the
noise generator.

*Homomorphic* *Encryption:* This allows the inference appli-cation on
the untrusted participant to directly perform DNN computations on
encrypted input \[52\], \[53\], so the sensitive information will not be
leaked. A drawback of homomorphic encryption is that it suffers from
huge inefﬁciency and is not applicable to all DNN operations.

> VI\. CONCLUSION

In this article, we explored the inference data privacy threats in
edge–cloud collaborative systems. We discovered that an untrusted cloud
can easily recover the inference sam-ples from intermediate values. We
proposed a set of new attack techniques to compromise the inference data
privacy under different attack settings. We demonstrated that the
adversary can successfully and reliably recover the inputs with very few
prerequisites.

We also proposed several methods to protect the infer-ence data privacy
for edge computing. Previous works, all focused on the performance,
efﬁciency, and functionalities of AIoT while ignoring privacy. We hope
that this study can raise awareness about the importance of inference
data privacy protection in edge–cloud systems and encourage the
balanc-ing of privacy protection with usability when designing or
implementing such systems.

> Authorized licensed use limited to: Universiteit van Amsterdam.
> Downloaded on May 19,2026 at 12:04:50 UTC from IEEE Xplore.
> Restrictions apply.

HE *et* *al.*: ATTACKING AND PROTECTING DATA PRIVACY IN EDGE–CLOUD
COLLABORATIVE INFERENCE SYSTEMS 9715

> REFERENCES
>
> \[1\] Z. He, T. Zhang, and R. B. Lee, “Model inversion attacks against
> col-laborative inference,” in *Proc.* *35th* *Annu.* *Comput.*
> *Security* *Appl.* *Conf.*, 2019, pp. 148–162.
>
> \[2\] Y. Tang, C. Zhang, R. Gu, P. Li, and B. Yang, “Vehicle detection
> and recognition for intelligent trafﬁc surveillance system,”
> *Multimedia* *Tools* *Appl.*, vol. 76, no. 4, pp. 5817–5832, 2017.
>
> \[3\] G. Chen, T. X. Han, Z. He, R. Kays, and T. Forrester, “Deep
> con-volutional neural network based species recognition for wild
> animal monitoring,” in *Proc.* *IEEE* *Int.* *Conf.* *Image*
> *Process.* *(ICIP)*, Paris, France, 2014, pp. 858–862.
>
> \[4\] C. Zhang, H. Li, X. Wang, and X. Yang, “Cross-scene crowd
> counting via deep convolutional neural networks,” in *Proc.* *IEEE*
> *Conf.* *Comput.* *Vis.* *Pattern* *Recognit.*, Boston, MA, USA, 2015,
> pp. 833–841.
>
> \[5\] L. Xiao, Y. Li, X. Huang, and X. Du, “Cloud-based malware
> detection game for mobile devices with ofﬂoading,” *IEEE* *Trans.*
> *Mobile* *Comput.*, vol. 16, no. 10, pp. 2742–2750, Oct. 2017.
>
> \[6\] F. Mireshghallah, M. Taram, P. Ramrakhyani, A. Jalali, D.
> Tullsen, and H. Esmaeilzadeh, “Shredder: Learning noise distributions
> to protect inference privacy,” in *Proc.* *25th* *Int.* *Conf.*
> *Archit.* *Support* *Program.* *Lang.* *Oper.* *Syst.*, 2020, pp.
> 3–18.
>
> \[7\] Z. He, T. Zhang, and R. Lee, “Sensitive-sample ﬁngerprinting of
> deep neural networks,” in *Proc.* *IEEE/CVF* *Conf.* *Comput.* *Vis.*
> *Pattern* *Recognit.*, Long Beach, CA, USA, 2019, pp. 4729–4737.
>
> \[8\] J. Hauswald, T. Manville, Q. Zheng, R. Dreslinski, C.
> Chakrabarti, and T. Mudge, “A hybrid approach to ofﬂoading mobile
> image classiﬁca-tion,” in *Proc.* *IEEE* *Int.* *Conf.* *Acoust.*
> *Speech* *Signal* *Process.* *(ICASSP)*, Florence, Italy, 2014, pp.
> 8375–8379.
>
> \[9\] Y. Kang *et* *al.*, “Neurosurgeon: Collaborative intelligence
> between the cloud and mobile edge,” *ACM* *SIGPLAN* *Notices*, vol.
> 52, no. 4, pp. 615–629, 2017.

\[10\] S. Teerapittayanon, B. McDanel, and H. Kung, “Distributed deep
neural networks over the cloud, the edge and end devices,” in *Proc.*
*IEEE* *Int.* *Conf.* *Distrib.* *Comput.* *Syst.*, Atlanta, GA, USA,
2017, pp. 328–339.

\[11\] J. H. Ko, T. Na, M. F. Amir, and S. Mukhopadhyay, “Edge-host
par-titioning of deep neural networks with feature space encoding for
resource-constrained Internet-of-Things platforms,” in *Proc.* *IEEE*
*Int.* *Conf.* *Adv.* *Video* *Signal* *Based* *Surveillance*, Auckland,
New Zealand, 2018, pp. 1–6.

\[12\] A. E. Eshratifar, M. S. Abrishami, and M. Pedram, “JointDNN: An
efﬁcient training and inference engine for intelligent mobile cloud
computing services,” 2018. \[Online\]. Available: arXiv:1801.08618.

\[13\] F. Mireshghallah, M. Taram, A. Jalali, A. T. Elthakeb, D.
Tullsen, and H. Esmaeilzadeh, “A principled approach to learning
stochastic represen-tations for privacy in deep neural inference,” 2020.
\[Online\]. Available: arXiv:2003.12154.

\[14\] (2018). *Torchvision.Datasets*. \[Online\]. Available: https:
//pytorch.org/docs/0.4.0/torchvision/datasets.html

\[15\] (2018). *Peak-Signal-to-Noise-Ratio*. \[Online\]. Available:
https: //en.wikipedia.org/wiki/Peak-signal-to-noise-ratio

\[16\] Z. Wang, A. C. Bovik, H. R. Sheikh, and E. P. Simoncelli, “Image
quality assessment: From error visibility to structural similarity,”
*IEEE* *Trans.* *Image* *Process.*, vol. 13, no. 4, pp. 600–612, Apr.
2004.

\[17\] L. I. Rudin, S. Osher, and E. Fatemi, “Nonlinear total variation
based noise removal algorithms,” *Physica* *D,* *Nonlinear* *Phenom.*,
vol. 60, nos. 1–4, pp. 259–268, 1992.

\[18\] F. Tramèr, F. Zhang, A. Juels, M. K. Reiter, and T. Ristenpart,
“Stealing machine learning models via prediction APIs,” in *Proc.*
*25th* *USENIX* *Security* *Symp.*, 2016, pp. 608–618.

\[19\] S. J. Oh, M. Augustin, M. Fritz, and B. Schiele, “Towards
reverse-engineering black-box neural networks,” in *Proc.* *Int.*
*Conf.* *Learn.* *Represent.*, 2018, pp. 2–3.

\[20\] B. Wang and N. Z. Gong, “Stealing hyperparameters in machine
learn-ing,” in *Proc.* *IEEE* *Symp.* *Security* *Privacy*, San
Francisco, CA, USA, 2018, pp. 36–52.

\[21\] X. Glorot and Y. Bengio, “Understanding the difﬁculty of training
deep feedforward neural networks,” in *Proc.* *13th* *Int.* *Conf.*
*Artif.* *Intell.* *Stat.*, 2010, pp. 249–256.

\[22\] C. Dwork, F. McSherry, K. Nissim, and A. Smith, “Calibrating
noise to sensitivity in private data analysis,” in *Proc.* *Theory*
*Cryptogr.* *Conf.*, 2006, pp. 265–284.

\[23\] C. Dwork and A. Roth, “The algorithmic foundations of
differential pri-vacy,” *Found.* *Trends* *Theor.* *Comput.* *Sci.*,
vol. 9, nos. 3–4, pp. 211–407, 2014.

\[24\] Y. Cheng, F. X. Yu, R. S. Feris, S. Kumar, A. Choudhary, and
S.-F. Chang, “An exploration of parameter redundancy in deep networks
with circulant projections,” in *Proc.* *IEEE* *Int.* *Conf.* *Comput.*
*Vis.*, Santiago, Chile, 2015, pp. 2857–2865.

\[25\] G. Ateniese, L. V. Mancini, A. Spognardi, A. Villani, D. Vitali,
and G. Felici, “Hacking smart machines with smarter ones: How to extract
meaningful data from machine learning classiﬁers,” *Int.* *J.*
*Security* *Netw.*, vol. 10, pp. 137–150, Sep. 2015.

\[26\] K. Ganju, Q. Wang, W. Yang, C. A. Gunter, and N. Borisov,
“Property inference attacks on fully connected neural networks using
permuta-tion invariant representations,” in *Proc.* *ACM* *Conf.*
*Comput.* *Commun.* *Security*, 2018, pp. 619–633.

\[27\] R. Shokri, M. Stronati, C. Song, and V. Shmatikov, “Membership
infer-ence attacks against machine learning models,” in *Proc.* *IEEE*
*Symp.* *Security* *Privacy*, San Jose, CA, USA, 2017, pp. 3–18.

\[28\] A. Salem, Y. Zhang, M. Humbert, M. Fritz, and M. Backes,
“Ml-leaks: Model and data independent membership inference attacks and
defenses on machine learning models,” in *Proc.* *Netw.* *Distrib.*
*Syst.* *Security* *Symp.*, 2018.

\[29\] S. Yeom, I. Giacomelli, M. Fredrikson, and S. Jha, “Privacy risk
in machine learning: Analyzing the connection to overﬁtting,” in *Proc.*
*IEEE* *Comput.* *Security* *Found.* *Symp.*, 2018, pp. 268–282.

\[30\] Y. Long *et* *al.*, “Understanding membership inferences on
well-generalized learning models,” 2018. \[Online\]. Available:
arXiv:1802.04889.

\[31\] J. Hayes, L. Melis, G. Danezis, and E. De Cristofaro, “LOGAN:
Membership inference attacks against generative models,” 2017.
\[Online\]. Available: arXiv:1705.07663.

\[32\] K. S. Liu, C. Xiao, B. Li, and J. Gao, “Performing co-membership
attacks against deep generative models,” 2018. \[Online\]. Available:
arXiv:1805.09898.

\[33\] L. Melis, C. Song, E. De Cristofaro, and V. Shmatikov,
“Exploiting unintended feature leakage in collaborative learning,” in
*Proc.* *IEEE* *Symp.* *Security* *Privacy*, San Francisco, CA, USA,
2019, pp. 691–706.

\[34\] M. Fredrikson, E. Lantz, S. Jha, S. Lin, D. Page, and T.
Ristenpart, “Privacy in pharmacogenetics: An end-to-end case study of
personalized warfarin dosing,” in *Proc.* *USENIX* *Security* *Symp.*,
2014, pp. 17–32.

\[35\] M. Fredrikson, S. Jha, and T. Ristenpart, “Model inversion
attacks that exploit conﬁdence information and basic countermeasures,”
in *Proc.* *ACM* *Conf.* *Comput.* *Commun.* *Security*, 2015, pp.
1322–1333.

\[36\] B. Hitaj, G. Ateniese, and F. Pérez-Cruz, “Deep models under the
GAN: Information leakage from collaborative deep learning,” in *Proc.*
*ACM* *Conf.* *Comput.* *Commun.* *Security*, 2017, pp. 603–618.

\[37\] C. Song, T. Ristenpart, and V. Shmatikov, “Machine learning
models that remember too much,” in *Proc.* *ACM* *Conf.* *Comput.*
*Commun.* *Security*, 2017, pp. 587–601.

\[38\] W. Hua, Z. Zhang, and G. E. Suh, “Reverse engineering
convolu-tional neural networks through side-channel information leaks,”
in *Proc.* *ACM/ESDA/IEEE* *Design* *Autom.* *Conf.*, 2018, pp. 1–6.

\[39\] Z. Yang, J. Zhang, E.-C. Chang, and Z. Liang, “Neural network
inversion in adversarial setting via background knowledge alignment,” in
*Proc.* *ACM* *SIGSAC* *Conf.* *Comput.* *Commun.* *Security*, 2019, pp.
225–240.

\[40\] L. Wei, B. Luo, Y. Li, Y. Liu, and Q. Xu, “I know what you see:
Power side-channel attack on convolutional neural network accelerators,”
in *Proc.* *Annu.* *Comput.* *Security* *Appl.* *Conf.*, 2018, pp.
393–406.

\[41\] R. Shokri and V. Shmatikov, “Privacy-preserving deep learning,”
in *Proc.* *ACM* *Conf.* *Comput.* *Commun.* *Security*, 2015, pp.
1310–1321.

\[42\] J. Hamm, A. C. Champion, G. Chen, M. Belkin, and D. Xuan,
“Crowd-ML: A privacy-preserving learning framework for a crowd of smart
devices,” in *Proc.* *IEEE* *Int.* *Conf.* *Distrib.* *Comput.* *Syst.*,
Columbus, OH, USA, 2015, pp. 11–20.

\[43\] O. Ohrimenko *et* *al.*, “Oblivious multi-party machine learning
on trusted processors,” in *Proc.* *25th* *USENIX* *Security* *Symp.*,
2016, pp. 619–636.

\[44\] T. Hunt, C. Song, R. Shokri, V. Shmatikov, and E. Witchel,
“Chiron: Privacy-preserving machine learning as a service,” 2018.
\[Online\]. Available: arXiv:1803.05961.

\[45\] Y. Cao and J. Yang, “Towards making systems forget with machine
unlearning,” in *Proc.* *IEEE* *Symp.* *Security* *Privacy*, San Jose,
CA, USA, 2015, pp. 463–480.

\[46\] M. Abadi *et* *al.*, “Deep learning with differential privacy,”
in *Proc.* *ACM* *Conf.* *Comput.* *Commun.* *Security*, 2016, pp.
308–318.

\[47\] R. Bost, R. A. Popa, S. Tu, and S. Goldwasser, “Machine learning
clas-siﬁcation over encrypted data,” in *Proc.* *Netw.* *Distrib.*
*Syst.* *Security* *Symp.*, 2015.

\[48\] T. Zhang, Z. He, and R. B. Lee, “Privacy-preserving machine
learning through data obfuscation,” 2018. \[Online\]. Available:
arXiv:1807.01860.

> Authorized licensed use limited to: Universiteit van Amsterdam.
> Downloaded on May 19,2026 at 12:04:50 UTC from IEEE Xplore.
> Restrictions apply.

9716

\[49\] A. Triastcyn and B. Faltings, “Generating artiﬁcial data for
private deep learning,” 2018. \[Online\]. Available: arXiv:1803.03148.

\[50\] X. Zhang, S. Ji, and T. Wang, “Differentially private releasing
via deep generative model (technical report),” 2018. \[Online\].
Available: arXiv:1801.01594.

\[51\] H. Yin *et* *al.*, “Dreaming to distill: Data-free knowledge
transfer via deepinversion,” 2019. \[Online\]. Available:
arXiv:1912.08795.

\[52\] R. Gilad-Bachrach, N. Dowlin, K. Laine, K. Lauter, M. Naehrig,
and J. Wernsing, “Cryptonets: Applying neural networks to encrypted data
with high throughput and accuracy,” in *Proc.* *Int.* *Conf.* *Mach.*
*Learn.*, 2016, pp. 201–210.

\[53\] C. Juvekar, V. Vaikuntanathan, and A. Chandrakasan, “GAZELLE: A
low latency framework for secure neural network inference,” in *Proc.*
*27th* *USENIX* *Security* *Symp.*, 2018, pp. 1651–1669.

> <img src="./vp0pmddj.png" style="width:1.00079in;height:1.25in" />**Zecheng**
> **He** (Student Member, IEEE) received the bachelor’s degree from the
> University of Science and Technology of China, Hefei, China, in 2015.
> He is currently pursuing the Ph.D. degree with the Department of
> Electrical Engineering, Princeton University, Princeton, NJ, USA.
>
> His research focuses on security and privacy in intelligent computer
> systems.
>
> IEEE INTERNET OF THINGS JOURNAL, VOL. 8, NO. 12, JUNE 15, 2021
>
> <img src="./x1o11v4u.png" style="width:0.99922in;height:1.25in" />**Tianwei**
> **Zhang** received the bachelor’s degree from Peking University,
> Beijing, China, in 2011, and the Ph.D. degree from Princeton
> University, Princeton, NJ, USA, in 2017.
>
> He is an Assistant Professor with the School of Computer Science and
> Engineering, Nanyang Technological University, Singapore. His research
> focuses on computer system security. He is par-ticularly interested in
> security threats and defenses in machine learning systems, autonomous
> systems, computer architecture, and distributed systems.
>
> <img src="./tqg3d4no.png" style="width:1.00079in;height:1.25in" />**Ruby**
> **B.** **Lee** (Life Fellow, IEEE) received the A.B. degree (with
> distinction) from Cornell University, Ithaca, NY, USA, and the Ph.D.
> degree in electri-cal engineering with a minor in computer science
> from Stanford University, Stanford, CA, USA.
>
> She is the Forrest G. Hamrick Professor of Engineering with Princeton
> University, Princeton, NJ, USA, where she is the Director of the
> Princeton Architecture Lab for Multimedia and Security (PALMS). Prior
> to Princeton University, she served as the Chief Architect with the
> Computer Systems

Division, Hewlett Packard, Silicon Valley, CA, USA. Her current research
is at the intersection of cyber security, computer architecture, and
deep learn-ing. Her research includes improving security with deep
learning, low-cost deep learning processors and designing new
architectures against attacks on microarchitecture, such as Spectre and
Meltdown. Her past research includes architectures for secure processors
and secure caches, and improving the security of smartphones and cloud
computing servers.

> Authorized licensed use limited to: Universiteit van Amsterdam.
> Downloaded on May 19,2026 at 12:04:50 UTC from IEEE Xplore.
> Restrictions apply.
