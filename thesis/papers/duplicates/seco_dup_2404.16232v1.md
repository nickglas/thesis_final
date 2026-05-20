> **DUPLICATE - do not cite separately.**
> This file is a duplicate copy of the SECO (Multi-Server Secure Inference) paper note.
> Canonical paper note: [../secure_inference/Secure Inference With Model Splitting Across Multi-Server Hierarchy.md](../secure_inference/Secure%20Inference%20With%20Model%20Splitting%20Across%20Multi-Server%20Hierarchy.md)
> Cite the canonical note only.

SECO: Secure Inference With Model Splitting
Across Multi-Server Hierarchy

Shuangyi Chenâˆ—, and Ashish Khisti âˆ—
âˆ—Department of Electrical and Computer Engineering, University of Toronto,
{shuangyi.chen@mail.utoronto.ca, akhisti@ece.utoronto.ca}

4
2
0
2

r
p
A
4
2

]

R
C
.
s
c
[

1
v
2
3
2
6
1
.
4
0
4
2
:
v
i
X
r
a

Abstractâ€”In the context of prediction-as-a-service, concerns
about the privacy of the data and the model have been brought
up and tackled via secure inference protocols. These protocols are
built up by using single or multiple cryptographic tools designed
under a variety of different security assumptions.

In this paper, we introduce SECO, a secure inference protocol
that enables a user holding an input data vector and multiple
server nodes deployed with a split neural network model to
collaboratively compute the prediction, without compromising
either partyâ€™s data privacy. We extend prior work on secure
inference that requires the entire neural network model to be
located on a single server node, to a multi-server hierarchy, where
the user communicates to a gateway server node, which in turn
communicates to remote server nodes. The inference task is split
across the server nodes and must be performed over an encrypted
copy of the data vector.

We adopt multiparty homomorphic encryption and multiparty
garbled circuit schemes, making the system secure against
dishonest majority of semi-honest servers as well as protecting
the partial model structure from the user. We evaluate SECO
on multiple models, achieving the reduction of computation and
communication cost for the user, making the protocol applicable
to userâ€™s devices with limited resources.

Index Termsâ€”Distributed machine learning, Security and

privacy

I. INTRODUCTION

Prediction-as-a-service using neural network models enables
a company to deploy a neural network on the cloud and
allows users to upload their input and obtain the correspond-
ing prediction results. However,
this may lead to privacy
concerns and legal issues. There are regulatory constraints
such as Health Insurance Portability and Accountability Act
(HIPAA) and EU General Data Protection Regulation (GDPR),
restricting the way data could be used or shared. A secure
inference protocol enables a user, holding its input, and
servers deployed with the neural network to collaboratively
evaluate the prediction result, preserving the privacy of both
the input and the model parameters. Many cryptographic
tools, such as Homomorphic Encryption (HE) [1] and secure
multiparty computation (MPC), have been applied in this area.
Homomorphic encryption allows the data holder to encrypt
its data with the public key, any other party who obtains the
encrypted data can compute on it without decryption, and only
the party holding the secret key can decrypt the computed
result. MPC is usually a mixed approach that combines secret
sharing and Garbled Circuit [2], etc. Both HE and MPC can
protect data privacy. Pure HE-based secure inference protocols
[3][4][5][6] provides the data and model confidentiality as well

as protects the structure of the model. However, it involves
heavy computation and does not immediately generalize to
non-linear function computations used during predictions. One
popular approach in HE-based protocols is to replace the
activation functions in neural networks with approximated
polynomials at the cost of reduced accuracy. While MPC
protocols are not as computationally heavy as HE-based
protocols,
they require multiple rounds of communication
and can also leak some information about the model to the
users. Furthermore, there are hybrid approaches that combine
HE and MPC. GAZELLE [7] relies on a hybrid approach
by employing HE and two-party computation, performing
linear function evaluation with HE and non-linear function
evaluation with Garbled Circuit. DELPHI [8] builds upon
techniques from GAZELLE and modifies it to a two-phase
protocol. It reduces the use of heavy cryptographic tools in
the online phase, thus speeding up online inference. However,
these methods come with certain limitations. Firstly,
they
reveal the neural networkâ€™s architecture to the user, which
is problematic when the modelâ€™s structure is intended to
remain confidential, a common scenario with todayâ€™s large
language models. Secondly, they require user equipment to
possess substantial computational power and communication
capabilities. Additionally, they operate under the assumption
that the model is hosted on a single server, which is impractical
for very large models. For instance, processing a model with
the size of GPT-4 necessitates a cluster of multiple GPUs.
To process such a large model effectively, distributing the
model parameters across several servers, each with limited
GPU resources, can enhance processing power.

With these considerations, we propose SECO, a hybrid HE-
MPC secure inference protocol that involves a hierarchy of
servers as shown in Figure 1. The user communicates with a
gateway server that stores a part (the parameters associated
with the first few layers) of the neural network model. The
remainder of the neural network model is stored on remote
servers, with each server holding a share of the weights
of the linear layers. Our setup extends the secure inference
protocol proposed in [8] to such a multi-server scenario,
which has several advantages. First, the user only needs to
participate during the evaluation involving part of the network
model stored on the gateway server. It does not need to
participate during evaluations involving the network model
stored on the remote servers. This reduces the communication
and computational requirements for the user device while

II. RELATED WORK

A. Privacy-Preserving Inference on Neural Networks

Secure Inference has received considerable attention in
recent years. It is developed based on the following techniques:
homomorphic encryption [9], secret sharing and garbled cir-
cuits [2]. Some earlier works utilize a single technique and
their models are simple machine learning models such as linear
regression [10] [11], linear classifiers [12] [13] [14], etc.

a) HE-based Protocols: Pure HE-based protocols usu-
ally protect the complete model information including the
architecture but lack support for non-approximated activation
functions. CryptoNets [3] was one of the earliest works to
use homomorphic encryption on neural network inference.
CryptoDL [4] improves upon CryptoNets by choosing the
interval and the degree of approximations based on heuristics
on the data distribution. CHET [5] also improves upon Cryp-
toNets by modifying the approximated activation function that
CryptoNets uses to f (x) = ax2 +bx with learnable parameters
a and b. TAPAS [6] utilizes FHE [15] to allow arbitrary-layer
neural network processing and proposes tricks to accelerate
computation on encrypted data. nGraph-HE [16] develops
HE-aware graph-compiler optimizations on general matrix-
matrix multiplication operations and convolution-batch-norm
operation. CHIMERA [17] uses different HE schemes for
ReLU functions and other neural network functions. It needs to
switch between two HE schemes to evaluate the model, leading
to high computational costs. Cheetah [18] presents a set of
optimizations to speed up HE-based secure inference, includ-
ing auto-tuning HE security parameters, the order scheduler
for HE operations, and a hardware accelerator architecture.
Pure HE-based protocols involve heavy computation and their
performance are not practical due to their costly homomorphic
computations.

b) MPC-based Protocols: Pure MPC-based protocols
are usually high-throughput but with high communication
overhead due to multiplication operations. Furthermore, they
usually need to expose the structure of the model to all parties.
ABY [19] is a 2PC protocol that supports arbitrary neural
network functions by combining Arithmetic, Boolean circuits,
and Yaoâ€™s garbled circuits. ABY3 [20] improves ABY by
extending it to 3-party settings and optimizing the conversion
between Arithmetic, Boolean circuits, and garbled circuits.
3PC protocol SecureNN [21] distributes 2-out-of-2 secret
sharing of the input among two of three servers. However,
it is only demonstrated on small DNNs. FALCON, a 3PC
protocol proposed by Wagh et al.[22] uses replicated secret
sharing to reduce the number of interactions. However, the
use of replicated secret sharing in the context of prediction-
as-a-service necessitates an increase in communication costs
for the user. To sum up, MPC-based protocols rely on as-
sumptions such as non-collusion, or an honest majority among
the servers. Such a strong assumption of the system might
not always align with the practical environments. Conversely,
SECO assumes dishonest majority among servers, meaning the
userâ€™s input privacy can be protected even when most of the

Fig. 1. Protocol Architecture

increasing the load on the servers, which enables the use of
SECO on lightweight user devices. Furthermore although as
in prior works [8], the structures of the layers in the neural
network model stored on the gateway server must be revealed
to the user, the structures of the layers on the remote server are
not revealed to the user. SECO offers the benefit of hiding most
of the neural networkâ€™s architecture, crucial for protecting the
proprietary structures of large models like GPT-4, where both
the modelâ€™s parameters and the modelâ€™s design are valuable
assets. We demonstrate that a straightforward application of
prior works to the hierarchical server setting can lead to
information leakage. Our proposed setting involves storing a
secret share of model weights at the remote server. However,
for secure inference of the partial model on the remote servers,
a straightforward extension of DELPHIâ€™s 2PC protocol
to
three-party setting with distributed weights is not privacy-
preserving due to the limitation of the plain HE scheme. To
privately perform the execution of secure inference on the
remote servers, we design a sub-protocol relying on multiparty
HE, secret sharing, and multiparty Garbled Circuit schemes,
ensuring the privacy of each individual data while facilitating
efficient communication. We achieve this by 1) designing new
secret sharing scheme and integrating it with multiparty HE
for secure computation of linear functions 2) departing from
the conventional approach for the use of Garbled Circuits (GC)
in DELPHI by redesigning the assignment of roles for secure
computation of non-linear functions. We formally demonstrate
that our proposed method prevents information leakage in the
presence of dishonest majority of honest-but-curious servers.
We have implemented SECO and reported the performance.
The results indicate that SECO significantly enhances effi-
ciency by reducing the userâ€™s online participation time by
up to 9.9Ã— and decreasing the userâ€™s online communication
costs by as much as 18.5Ã— compared to DELPHI. It also
provides a versatile tradeoff between the communication and
computation loads between the user and server in addition to
protecting more information about the neural network than
prior works [8].

Gateway serverRemote serversThe userServer AServer BServer Cservers are corrupted by the adversary. Thus, SECO can offer a
higher degree of trustworthiness to users than pure MPC-based
protocols. Furthermore, these 3PC protocols require the user to
divide the input into multiple random shares. Each input share
is then dispatched to three different servers, thereby increasing
the communication costs for the user.

c) HE-MPC-based Protocols: HE-MPC-based Protocols
are designed by using both HE and MPC in a hybrid scheme.
GAZELLE [7] designs schemes for HE neural network opera-
tions. It uses HE to evaluate linear layers and Garbled Circuits
to evaluate non-linear layers, achieving efficient secure infer-
ence with high accuracy. DELPHI [8] modifies GAZELLE by
designing two phases with the offline phase using HE, speed-
ing up the online inference by evaluating the neural network in
plaintext. It also proposes a novel neural network architecture
search planner to determine where to approximate ReLU in the
neural network, trading off between performance and accuracy.
MP2ML [23] is proposed based on a novel combination of
nGraph-HE [16] and ABY [19], combining additive secret
sharing and CKKS [24] HE scheme. However, HE-MPC-based
Protocols face several limitations. Firstly, they require reveal-
ing the neural networkâ€™s architecture to users, problematic for
confidential models like large language models. Secondly, they
demand substantial computational power and communication
capabilities from user equipment, which can be a barrier for
those with limited resources. Thirdly, these methods assume
the model is hosted on a single server, impractical for large
models like GPT-4 that need multiple GPUs. SECO is derived
from these 2PC HE-MPC-based Protocols and is optimized to
address the mentioned limitations.

B. Split Neural Network

Split neural network is a specific type of neural network
architecture. In this method, the neural network is divided
into two or more sections, and each section is processed on
different devices or servers. It is often used to reduce load for
devices with limited resources. SplitFed [25] is a federated
learning framework that combines federated learning with
split learning for better model privacy. However, it applies
differential privacy rather than cryptographic tools. Pereteanu
et al. introduce Split HE [26], a framework where the server
provides the user with the middle portion of the neural
network. In this setup, the user conducts plaintext inference on
the middle section of the network, while the server manages
the inference of other parts under homomorphic encryption.
However, this approach harms the privacy of the deployed
model. Khan et al. propose a secure training protocol named
Split Ways [27] based on U-shaped split
learning, which
incorporates homomorphic encryption on the client side to
protect user input privacy. However, while they deploy only the
fully-connected layer on the server, the user is still responsible
for training the majority of the neural network. Split HE and
Split Ways explore the integration of split neural networks
with cryptographic tools. However, they do not fully utilize
the serverâ€™s computing resources and continue to depend
significantly on the userâ€™s device.

III. PRELIMINARIES

A. Split Neural Network

Split Neural Network [28][29] involves splitting a neural
network model at different intermediate layers. Consider a
neural network function F composed of a sequence of layers
{F1, ..., FL}. Each layer Fi can be a linear layer or an activa-
tion layer. The prediction result of the model for a given input
x1 can be computed by F(x1) = FL(FLâˆ’1(...(F1(x1)))).
the lth
We split
two models
FI = {F1, ..., Fl}, FII = {Fl+1, ..., FL} which could be
stored at two different nodes. The output can be expressed as
F(x1) = FII (FI (x1)). We adjust l to adjust the processing
(training or inference) load for the parties deployed with FI
and FII .

the model at

layer to get

B. Cryptographic Blocks

We use the following cryptographic blocks to build the

protocol.

1) The Plain BFV Homomorphic Encryption: The
Brakerskil-Fan-Vercauteren scheme [1] is a Ring-Learning
with Errors (RLWE)-based cryptosystem that supports additive
and multiplicative homomorphic operations. We define the
plaintext space to be Rt = Zt[X]/(X n +1) and the ciphertext
space to be Rq = Zq[X]/(X n + 1), where n is a power
of 2. We denote âˆ† = âŒˆ q
t âŒ‰. BFV Homomorphic Encryption
scheme can be expressed as a tuple of
functionalities
HE = (HE.KeyGen, HE.Enc, HE.Dec, HE.Eval). The
the key
scheme is based on two kinds of distributions:
distribution R3 = Z3[X]/(X N + 1) with coefficients
uniformly distributed in {âˆ’1, 0, 1}; the error distribution Ï‡
over Rq with coefficients distributed according to a centered
discrete Gaussian.

â€¢ HE.KeyGen(Params) â†’ (pk, sk):It

takes a security
parameter as input and returns a public key pk and a
secret key sk.

Algorithm 1 HE.KeyGen(params) â†’ (pk, sk)
1: Sample s â† R3
2: Let sk = s. Sample p1 â† Rq, e â† Ï‡
3: pk = (p0, p1) = (âˆ’sp1 + e, p1). Output (pk, sk)

â€¢ HE.Enc(pk, m) â†’ ct: It takes as input the public key pk
and message m, and outputs the ciphertext of m denoted
as ct.

Algorithm 2 HE.Enc(pk, m) â†’ ct
1: Let pk = (p0, p1). Sample u â† R3, e0, e1 â† Ï‡
2: Output ct = (âˆ†m + up0 + e0, up1 + e1)

â€¢ HE.Dec(sk, ct) â†’ m: It takes as input the secret key sk

and the ciphertext ct, and outputs message m.

Algorithm 3 HE.Dec(sk, ct) â†’ m
1: Let sk = s, ct = (c0, c1)
2: Output m = [âŒŠ t

q [c0 + c1s]qâŒ‰]t

â€¢ HE.Eval(pk, {cti, pti}, f ) â†’ ctf : It takes as input the
public key pk, valid ciphertexts {cti} encrypting {mi}
or plaintexts {pti} encoding {mi} and operation f , and
returns a valid ciphertext ctf encrypting f ({mi}i). The
class of function f (Â·) that are supported include element-
wise addition Add, subtraction Sub and multiplication
Mul and slot rotation Rot, as well as a combination of
those basic operations.

2) Multiparty BFV Homomorphic Encryption (MPHE):
The Multiparty version of BFV Homomorphic Encryption
scheme (MPHE) [30] is extended from the plain BFV scheme.
It enables multiple distributed parties, each with input
in
private, to collaboratively compute a function of those inputs
without leaking any partyâ€™s input. In this scheme, a common
public key collectively generated by parties is known to all
parties, while the corresponding secret key csk is distributed
among parties. Below we introduce the main functions used
in the protocol. Consider a scenario that N parties want to
collaboratively compute a function of their private inputs.

â€¢ MPHE.KeyGen(params) â†’ (pki, ski) :Each party runs
HE.KeyGen(params) and generates a public key pki
and secret key ski. This procedure requires a public
polynomial p1, which is agreed upon by all N parties.

â€¢ MPHE.DKeyGen({pki}N âˆ’1

i=0 ) â†’ cpk :It returns a com-
mon public key cpk, for a set of public keys {pki}N âˆ’1
i=1 .
Its corresponding secret key csk is the aggregation of
{ski}N âˆ’1
i=1 .

Algorithm 4 MPHE.DKeyGen({pki}N âˆ’1
1: Let pki = (p0,i, p1)
2: Output cpk = ([(cid:80)N âˆ’1

i=0 p0,i]q, p1)

i=0 ) â†’ cpk

â€¢ MPHE.Enc(cpk, m) â†’ ct :It returns a ciphertext ct by

running HE.Enc(cpk, m).

â€¢ MPHE.Eval(cpk, {cti, pti}, f ) â†’ ctf :It returns a ci-
phertext ctf by running HE.Eval(cpk, {cti, pti}, f ).
â€¢ MPHE.Reconstruct(ct, ski) â†’ pdi :Used by each party
i. It takes as input a publicly known ciphertext ct, partyâ€™s
secret key ski, outputs a partial decryption pdi.

Algorithm 5 MPHE.Reconstruct(ct, ski) â†’ pdi
1: Let ski = si, ct = (c0, c1). Sample ei â† Ï‡
2: Output pdi = sic1 + ei

â€¢ MPHE.Dec({pdi}N âˆ’1

i=0 , ct) â†’ mâ€²: It
takes as input
a set of partial decryption {pdi}N âˆ’1
and the corre-
i=0
sponding publicly known ciphertext ct. By aggregating
the partial decryption, it outputs mâ€² which is equal to
HE.Dec(ct, csk), provided that
the noise powers are
again selected in a suitable manner.

3) Oblivious Transfer (OT): Oblivious transfer [31] [32] is
a protocol involving two parties, a sender who has an input
two messages m0, m1, and a receiver who holds a bit b as
input. Via OT, the receiver obtains mb. The security of the
protocol guarantees that the sender does not learn anything

Algorithm 6 MPHE.Dec({pdi}N âˆ’1
1: Let ct = (c0, c1)
2: Compute

i=0 , ct) â†’ mâ€²

c0 + c1s = c0 +

N âˆ’1
(cid:88)

i=0

pdi = c0 + c1(

N âˆ’1
(cid:88)

i=0

si) +

N âˆ’1
(cid:88)

i=0

ei

3: Output mâ€² = [âŒŠ t

q [c0 + c1s]qâŒ‰]t

about bit b and the receiver does not learn anything about the
message m1âˆ’b.

4) Garbled Circuits: A Garbled Circuit scheme [2] [33] is
a cryptographic tool involving two parties joint computing a
function C(x1, x2) where x1 and x2 are inputs provided by
the garbler and the evaluator. The scheme should keep the
inputs fully private. It is consists of a tuple of algorithms
GC=(GC.Garble, GC.Transfer, GC.Eval) with the following
syntax:

â€¢ GC.Garble(Params, C) â†’ ( ËœC, label): Used by the
garbler. Assume C is composed of G gates (e.g., XOR,
AND, etc.) in total. The garbler garbles the circuit by
1) Assigning two random k-bit labels to each wire in
the circuit C corresponding to 0 and 1 where k is
the security parameter usually set to 128; 2) For each
gate g, g âˆˆ [G] in C, computing a garbled table ËœCg
with 4 rows corresponding to 4 combinations of inputs
labels. Each row is the encryption of the output with two
corresponding input labels as the encryption key [34].
Output ËœC = { ËœCg}Gâˆ’1
g=0 and labels corresponding to input
wires label.

â€¢ GC.Transfer(label, xi) â†’ labelxi

: This function in-
volves both the garbler and the evaluator. If i = 2, for
input x2 held by the garbler, the garbler maps x2 with
the labels generated for input wire corresponding to x2
to obtain labelx2 , then sends labelx2 to the evaluator.
If i = 1, for input x1 held by the evaluator,
the
evaluator cannot simply send x1 to the garbler to obtain
labelx1 . This undermines input privacy. The garbler and
the evaluator engage in an OT protocol where the garbler
provides labels for inputs wires belonging to the evaluator
and the garbler provides the bit-expression of x1. The
evaluator will receive the labels corresponding to x1
without exposing x1 to the garbler via OT. This step
outputs the correct labels labelxi corresponding to actual
input xi.

â€¢ GC.Eval( ËœC, {labelxi}iâˆˆ{1,2}) â†’ y: Used by the eval-
uator. The evaluator starts from the first gate and uses
two input labels with the garbled table ËœC0 to obtain the
output. Then the evaluator performs the evaluation for
each gate in order until obtaining the output y of the last
gate, where y = C(x1, x2).

A two-party Garbled Circuit scheme can be easily extended
to a multiparty computations scheme of arbitrary complexity
with an arbitrary number of participants providing inputs. The
input providers obtain the labels for their private inputs via OT

from the garbler, then they transmit the labels to the evaluator,
which reveals nothing about the inputs since the labels are
random.

5) Additive Secret Share: Let q be a prime. A 2-of-2
additive secret sharing of x âˆˆ Zq is a pair (âŸ¨xâŸ©1, âŸ¨xâŸ©2) =
(xâˆ’r, r) âˆˆ Z2
q for a random r âˆˆ Zq such that x = âŸ¨xâŸ©1+âŸ¨xâŸ©2.
Additive secret sharing is perfectly hidden, for example, given
a share âŸ¨xâŸ©1 or âŸ¨xâŸ©2, the value x is perfectly hidden. n-of-
n additive secret sharing can be easily extended from 2-of-2
additive secret sharing. A n-of-n additive secret sharing of x âˆˆ
Zq can be constructed by generating (r1, ..., rnâˆ’1) âˆˆ Znâˆ’1
uniformly at random and setting rn = x âˆ’ (cid:80)nâˆ’1
i=1 ri(mod q).

q

C. Prior Work: DELPHI

Here we describe the protocol we built upon: DELPHI [8].
DELPHI is a cryptographic neural network inference protocol.
There are two parties in the system of DELPHI: the user
and the server. DELPHI uses additive secret sharing pre-built
with homomorphic encryption to evaluate linear layers, and
garbled circuits pre-built to evaluate activation functions. Let
F = {Fi}L
i=1 described in Section III-A be the deployed
model on the server, xi = Fiâˆ’1(Fiâˆ’2(...(F1(x1)))) is the the
intermediate prediction result of the first i âˆ’ 1 layers where
x1 âˆˆ Zq is the input held by the user.

In the preprocessing phase, the client and the server pre-
compute the secret share which will be used for the inference
phase. For each linear layer i âˆˆ [L], with the user providing the
ciphertext of ri and the server providing the plaintext of Fi and
si, two parties interact to compute Firiâˆ’si where ri and si are
the random masks for building secret shares, resulting in each
of the party holding one of the two secret shares of Firi. For
ReLUs following linear layers, the server constructs a garbled
circuit ËœCi based on circuit C computing ReLU function. Then
the server transmits ËœCi to the user and input labels of Firi âˆ’si
and ri+1 via Oblivious Transfer to the user. We note that the
algorithm for computing the ciphertext of Firi in DELPHI
relies on GAZELLEâ€™s design [7] for HE linear operations
(convolutional and fully-connected layer). We do not provide
details of this algorithm but represent it as a function Lin-
OP. With function Lin-OP, ciphertext ctri encrypting ri and
plaintext ptFi encoding Fi as input, HE.Eval will output the
ciphertext of Firi.

In the inference phase, assuming xi is the prediction result
of the first i âˆ’ 1 layers, at the beginning of the ith layer, the
server and the user hold the shares of xi: xi âˆ’ ri and ri. The
server evaluates to get Fi(xi âˆ’ ri) + si, resulting in the server
and the user holding the secret shares of Fixi. For evaluating
ReLU, the server transmits the input labels corresponding to
its secret share to the user. Then the client evaluates ËœCi to
obtain a secret share of the ReLU output.

IV. SECURE INFERENCE: HIERARCHICAL SERVER
CONFIGURATIONS

Our proposed setup involves splitting the neural network
model across three server nodes. We assume that the user
communicates with a gateway server that holds part of the

neural network model. The remainder of the model is stored
on remote servers that do not directly communicate with the
user. One motivation for considering such a scenario is that
the interactions of the user and the server are required in
computing each layer in the DELPHI protocol. This increases
the computational and communication load on the user. Fur-
thermore, the user gets access to information about the neural
network including the shape of each layer and the total number
of model layers since the user needs to generate randomness
for each linear layer to build up additive secret shares, which
is undesirable. By deploying a subset of the model on remote
servers that do not directly interact with the user we can
partially address these concerns.

A. Baseline Configuration

We now explain why a straightforward extension of the
DELPHI protocol that splits the neural network model across
two server nodes as shown in Fig. 2 will lead to information
leakage. In this setting, the user and the gateway server as
well as the gateway server and the remote server respectively
execute DELPHI to evaluate the two split models in order as
Figure 2 shows. In this case, the user can be offline when two
servers evaluate the second split model and the architecture of
the second split model can be kept secret from the user.

Let us consider deploying FI , FII

(described in Sec-
tion III-A) on server A and B respectively. When evaluating
FII involving server A and B, server B holds the masked
intermediate prediction result xi âˆ’ ri while randomness ri is
only contributed by server A. Note that if the two servers
collude to recover xi they can get access to full parameters
of the first i âˆ’ 1 layers, then execute the white-box model
inversion attack proposed in [35] to reconstruct the userâ€™s
input.

Fig. 2. DELPHI extended to Split Neural Network

B. Proposed Scheme

We consider a setting with a hierarchy of servers where there
are a gateway server and two remote servers as Figure 1 shows.
We deploy FI on the gateway server A and the processing
of it follows DELPHI. For the second split model FII , the
linear layers are randomly divided into 2 shares. We distribute
the shares among 2 remote servers. We summarize the main
advantages of our proposed architecture as follows: 1) hide
partial architecture information of the model from the user

Gateway Server RemoteServerThe userDelphiDelphiand reduce the userâ€™s computation and communication cost 2)
defend the possible white-box model inversion attack resulting
from the model leakage and intermediate prediction result
recovery caused by server collusion. We give the detailed
description of the protocol in Section VI.

V. SYSTEM OVERVIEW
As shown in Figure 1, there are four parties in our setting: a
user, and hierarchical service providers including server A, B,
and C. The hierarchy contains two layers of servers: gateway
server A in the first layer, and server B and C in the second
layer. Three servers cooperate to provide prediction service of
a model F. The model F can be expressed as F = (FA :
{Fi}iâˆˆ{1,...,l}, FBC : {Fi}iâˆˆ{l+1,...,L}) where L is the total
number of model layers. Server A holds the first l layers FA.
For ith layer i âˆˆ {l + 1, ..., L}, Server B and C hold the
random share of linear layer Fi, which can be expressed as
Fi = (cid:80)3
A. Threat Model and Privacy Goals

i (j = 2 for server B, j = 3 for server C).

j=2 Fj

a) Threat model.: We assume a passive-adversary model
with corruption of a user or up to two servers (any two). The
parties will not deviate from the protocol but the adversary
can corrupt the user or up to 2 servers so can know corrupted
partiesâ€™ private data and the observations. We assume the
adversary cannot corrupt the user and the server simultane-
ously. Additionally, we assume server A belongs to the service
provider while server B and C are external. Deployment of
random shares on external servers wonâ€™t compromise the
proprietary model privacy.

b) Privacy Goals.: For the user, we aim to design a
protocol that enables the user to only learn the result of the
inference and the architecture of the model on gateway server
A. All other information about the model including the model
parameters, the total number of layers, and the architecture of
the layers on server B, C should be kept secret from the user.
Assuming up to 2 servers corrupted by the adversary, we
have the privacy goals for the servers as the followings:
1) the adversary should not learn any honest partyâ€™s model
parameters or the intermediate prediction result xi; 2) the
adversary should not infer the userâ€™s input.

VI. THE PROTOCOL: FORMAL DESCRIPTION
In this section, we introduce our secure inference protocol.
The protocol takes as input the userâ€™s data x1 âˆˆ Zq and the
split model (FA = {Fi}iâˆˆ{1,...l}, FBC = {Fi}iâˆˆ{l+1,...L}),
and enables four parties to execute secure inference collabo-
ratively. The protocol can be considered as the combination of
a 2-PC protocol, executed between the user and the gateway
server for the inference of FA, and a 3-PC protocol, executed
between the gateway server and two remote servers for the
inference of FBC. The 2-PC protocol is adapted from DELPHI
[8] and the 3-PC protocol is designed to achieve the secure
neural network computations in the presence of dishonest
majority of honest-but-curious servers. The protocol consists
of three phases as shown in Figure 3: a setup phase, a
preprocessing phase, and an online inference phase.

Fig. 3. SECOâ€™s 3 phases

A. Setup Phase

The setup phase is executed before the user appears in the

system.

1) Key Generation: This step is to generate keys for ho-

momorphic computation.

1) Each server runs HE.KeyGen to generate key pair
(skj, pkj) (j = 0 for the user, j = 1 for server A,
j = 2 for server B, j = 3 for server C).

2) Server A collects the public keys from the three servers,
runs MPHE.DKeyGen to obtain a common public key
cpk, then transmits cpk to the user, server B and C.

At the end of the step, each server holds a common public
key cpk.

2) Model Preparation: : This step is the preparation for
FBC which can be executed before the user appears in the
system. Like in DELPHI, the key insight is to pre-compute the
additive secret shares of Firi for each linear layer of FBC.
Server A, B, and C collaboratively compute the secret shares
of Firi with MPHE scheme, where Fi is distributed among
server B and C and the randomness ri is solely contributed by
the user if i = l + 1 or jointly contributed by three servers if
i âˆˆ {l + 2, ..., L}. The preprocessing of the l + 1th linear layer
is required for a secure transition from the inference of FA
to FBC. Additionally, three servers construct garbled circuits
for each activation layer in FBC.

a) Preprocessing for other linear layers.: For the ith
layer i âˆˆ {l + 2, ...L}, server A, B, and C contribute to the
randomness ri and collaborate to compute three secret shares
of (F2
l+1)rl+1 . With server B and C providing the
ciphertexts of private model parameter Fj
i , input randomness
i and output randomness sj
rj
i , server A computes its share
i ) âˆ’ s2
i + r3
i )(r1
i = (F2
E1
i , resulting in building

l+1 + F3

i + F3

i + r2

i âˆ’ s3

Server AServer BServer CSetupMPHE key generationPreprocessing of ð‘­ð‘©ð‘ªServer AServer BServer CPreprocessingPreprocessing of ð‘­ð‘¨Server AServer BServer CInference of ð‘­ð‘¨Inference of ð‘­ð‘©ð‘ªi )(r1

i + r3

i + r2

i + F3

the additive shares of (F2
i ) among three
servers. See Algorithm 8 for details. In Algorithm 8, we use
MPHE.DisDec (Algorithm 7) which is a protocol for the
distribute decryption of MPHE scheme involving three servers.
b) Preprocessing for activation layers: Three servers
collaborate to build the garbled circuit on server A and prepare
the evaluation of the activation layers. With server B as the
garbler, server C as the evaluator, and server A providing input
as the third party, server B first prepares the garbled circuit
ËœCi and labels by running GC.Garble(Params, Ci) where
Params is the security parameters and Ci is described in
Algorithm 9. To transmit the labels corresponding to actual
input values, server B sends the labels of the input value
provided by itself to server C through a public channel. For
input values from server A and C, server A and C first obtain
the actual labels from server B via OT. Then server C collects
the labels obtained by server A through a public channel.

B. Preprocessing Phase

In the preprocessing phase, the user first generates a key pair
(sk0, pk0) and broadcasts pk0 to each server in the system
through Server A. Server A sends common public key cpk
to the user. For preprocessing of FA, the user and server
A collaboratively pre-compute the secret shares of weights
for linear layers and construct garbled circuits for activation
layers.

1) Preprocessing for FA: This step follows the approach

in DELPHI.

a) Preprocessing for linear layers.: For the ith linear
layer i âˆˆ [1, ..., l], with the user providing the ciphertext of ri,
server A computes the ciphertext of Firi âˆ’ si where ri is the
randomness of the layerâ€™s input size and si is the randomness
of the layerâ€™s output size, then the user decrypts it using sk0,
resulting in the user holding Firi âˆ’ si and server A holding
si which are two additive shares of Firi.

b) Preprocessing for activation layers.: After the prepro-
cessing for linear layers, the user and server A collaborate to
build the garbled circuits for activation layers in FA. Ci is
the circuit to compute the activation function. Server A will
execute GC.Garble to generate a set of the garbled tables ËœCi
according to gates in circuit Ci and labels corresponding to
all input wires in Ci. Then server A transmits the labels for
actual input values to the user. For input values held by server
A such as one-time password di+1, server A generates labels
based on the bit expression of di+1 and directly sends it to the
user. For input values held by the user such as Firi âˆ’ si, ri+1,
server A and the user engage in OT protocol to let the user
obtain the corresponding labels without server A knowing the
actual value.

c) Preprocessing for the l +1th linear layer.: In this step,
the protocol involves 4 parties to prepare for the transition
from the inference of FA to FBC. The user, server A, B, and
C collaborate to build the additive shares of (F2
l+1)rl+1
among three servers, that is, with server B and C providing the
ciphertexts of their own Fj
l+1 and the ciphertxts of the output
randomness sj
i+1, with the user providing the ciphertext of

l+1+F3

the plain secret key

Algorithm 7 MPHE.DisDec

the ciphertext of m; skj:

Inputs: ct:
generated by the contributor of cpk
Server A:

Transmit ct to server B and C
MPHE.Reconstruct(ct, sk1) â†’ pd1

Server B and C:

MPHE.Reconstruct(ct, skj) â†’ pdj
Transmit pdj to server A

Server A:

Run MPHE.Dec(ct, {pdj}{jâˆˆ{1,2,3}}) to obtain m

l+1 + F3

input randomness rl+1, server A homomorphically computes
the ciphertext of El+1 = (F2
l+1
and then involves server B and C to decrypt it. At the end of
the preprocessing of the l + 1th linear layer, three server holds
the respective secret share of (F2
l+1)rl+1. Note all the
encryption in this stage are conducted with MPHE public key
cpk.

l+1)rl+1 âˆ’ s2

l+1 + F3

l+1 âˆ’ s3

Algorithm 8 Pre-Compute the share for the ith linear layer,
i âˆˆ {l + 2, ...L}

Inputs: (qi, wi): the input and output shape of the ith layer; cpk:
common public key
Server A:
i â† Zqi
r1
q
Compute ctr1
Server B and C:
q , sj
rj
i â† Zwi
i â† Zqi
ctrj
Compute
MPHE.Enc(cpk, sj
Transmit (ctrj

q
= MPHE.Enc(cpk,rj
i ),
= MPHE.Enc(cpk, Fj
i )

= MPHE.Enc(cpk,r1
i )

i ), ctF j
, ctsj

) to server A

, ctF j

ctsj

=

i

i

i

i

i

i

i

Server A:

i

i

i

, Add)â†’ ctFi
, Add)â†’ ctsi
, ctr3

, ctF 3
MPHE.Eval(ctF 2
, cts3
MPHE.Eval(cts2
, Add)â†’ ctri
, ctr2
MPHE.Eval(ctr1
MPHE.Eval(ctFi , ctri , Lin-OP)â†’ ctFiri
MPHE.Eval(ctFiri , ctsi , Sub) â†’ ctFiriâˆ’si
Transmit ctFiriâˆ’si to server B and C

i

i

i

i

Server A, B, C:

Run MPHE.DisDec(ctFiriâˆ’si , {skj}jâˆˆ{1,2,3})
i âˆ’ s3
Server A obtains Ei = (F2

i )ri âˆ’ s2

i + F3

i where ri =

i + r2
r1

i + r3
i

C. Online Inference Phase

This section introduces the inference phase in the order of
model layers. First, as preamble, the user computes x1 âˆ’ r1
and sends it to server A.

a) Inference of FA: The inference of FA involves the
participation of the user and server A. Before evaluating the
ith, i âˆˆ [1, ..., l] layer, server A holds the masked input xi âˆ’ ri
and the user holds the input randomness ri+1 for next layer.
Server A first computes Fi(xi âˆ’ ri) + si to evaluate the linear
part and sends the labels of it to the user. Collecting the labels
of all the input wires in ËœCi, the user executes GC.Eval to
obtain a masked ReLU output as the masked input for the
next layer.

Algorithm 9 A circuit Ci that computes ReLU function of
the ith layer i âˆˆ {l + 1, ..., L}
Input from server A: (F2
Input from server B: F2
Input from server C: F3

i + F3
i )ri âˆ’ s2
i (xi âˆ’ ri) + s2
i (xi âˆ’ ri) + s3

i , r1

i+1

i âˆ’ s3
i , r2
i+1
i , r3
i+1
i )ri âˆ’ s2

i âˆ’ s3

i + F2

i (xi âˆ’

i )xi = (F2

1: Compute (F2
ri) + s2
i + F3

i + F3
i (xi âˆ’ ri) + s3
i
i + F3
2: Compute xi+1 = ReLU ((F2
3: Output xi+1 âˆ’ ri+1 = xi+1 âˆ’ r1

i + F3

i )xi)
i+1 âˆ’ r2

i+1 âˆ’ r3

i+1

TABLE I
THE COLUMNS DEPICT THE THREE DISTINCT SEGMENTS OF THE
DEPLOYED MODEL, EACH ILLUSTRATING CONTRIBUTIONS FROM THE
INVOLVED PARTIES AND DIFFERENT COMPUTATIONAL GOALS.

FA

ri

Fi,si

User

Server A

Server B

Server C

FBC

Transition

ri

r1
i
i ,s2
r2
i ,F2
i
i ,s3
r3
i ,F3
i
i + r2
i )(r1
i + F3
i + s3
âˆ’(s2
i )

(F2

i + r3
i )

F2

i ,s2
i
F3
i ,s3
i
i + F3
i )ri
i + s3
i )

(F2
âˆ’(s2

b) Transition: After the evaluation of FA, server A holds
xl+1 âˆ’ rl+1. Server A forwards it to server B and C as a
transition step from the inference of FA to FBC.

Shares
to compute

Firi âˆ’ si

c) Inference of FBC: The inference of FBC involves
the participation of server A, B, and C. At the beginning of
the inference for ith layer i âˆˆ {l + 1, ..., L}, server B and C
hold xi âˆ’ ri where ri is solely contributed by the user when
i = l + 1, and is contributed by server A, B and C for linear
other layers of FBC. Server A, B and C collaborate to do
inference on ith layer i âˆˆ {l + 1, ..., L}. First server B and
C will compute Ej
i , resulting in three
servers holding three additive shares of the real prediction
i )xi. The garbled circuit ËœCi
result for the current layer (F2
i +F3
(Algorithm 9) first aggregates shares to recover (F2
i )xi,
then computes ReLU of it, finally masks the ReLU output with
the randomness of the next layer contributed by three servers.
The entire process is in the encrypted domain. The garbled
circuit for each ReLU layer of FBC are located at server C.
Thus server C can evaluate the garbled circuit when collecting
all labels for input wires of ËœCi in a secure way.

i (xi âˆ’ ri) + sj

i = Fj

i + F3

Algorithm 10 Inference for the ith layer, i âˆˆ {l + 1, ..., L}

, labelr2

the garbled
label: random labels for
i+1: randomness from server A;
: labels for actual input values held

in Algorithm 9;

Inputs: xi âˆ’ ri: held by server B and C; ËœCi:
circuit of circuit
input wires of Algorithm 9; r1
labelE1
i
by server A
Server B and C:
Compute Ej
GC.Transfer(label, E3
Server C obtains labelE3

i (xi âˆ’ ri) + sj
i )â†’ labelE3

i = Fj

, labelr3

i+1

i+1

i

i

i

Server C:

GC.Eval( ËœCi, labelE2
) â†’ xi+1 âˆ’ r1

i

labelr2

i+1

i+1 âˆ’ r2

i+1

, labelE3

, labelE1

i

, labelr1

i+1

,

i

Compute xi+1 âˆ’ ri+1 = xi+1 âˆ’ r1
Transmit xi+1 âˆ’ ri+1 to server B

i+1 âˆ’ r2

i+1 âˆ’ r3

i+1

D. Output

After the evaluation of FBC, server A holds the share (F2
F3
L)rL âˆ’s2
C holds F3

L âˆ’s3
L(xL âˆ’ rL) + s3
L.

L, server B holds F2

L(xL âˆ’rL)+s2

L+
L and server

1) Server B and C computes HE.Enc(pk0, Fi
si
L) and sends this ciphertext to server A.

L(xL âˆ’ rL) +

2) Server A homomorphically add the received ciphertext
to compute the ciphertexts ctË†y of prediction result Ë†y
where Ë†y = (F 2
L)xL, then transmits ctË†y to the user.

L + F 3

3) The user decrypts ctË†y with sk0 to obtain the prediction

result Ë†y.

E. Discussion

We next highlight key technical contributions and the mo-

tivations for our design choices.

a) Secret Sharing for 3PC and Integration with MPHE:
To sum up, during the executions,
the protocol processes
model FA and FBC. The processing of FA follows DELPHI
which uses plain HE scheme to build two secret shares of
Firi among two parties in the preprocessing phase, where ri
is randomly generated by the user; In the inference phase, ri
will be used as the mask for the intermediate prediction result
xi and it can be canceled by the secret share built in the
preprocessing phase. Our protocol follows this idea to build
three secret shares of {Firi}L
i=l+1 in the preprocessing phase
of FBC, where each of the servers contributes its own part
to the randomness ri. However, using a plain HE scheme to
compute the secret shares is not privacy-preserving in this case
because the model parameters and randomness are distributed.
To ensure that each of the three servers exclusively accesses
its designated information and no extraneous data, we design
a new secret sharing scheme as in Table I, so the shares can
be computed with MPHE using the supported operations as
described in Section III-B1, enabling secure computation of
linear functions.

b) Assignments of Servers in GC: For the secure com-
putation of non-linear functions, we deviate from the con-
ventional approach of assigning the layerâ€™s input provider
as the evaluator in Garbled Circuits (GC), like in DELPHI.
Instead, we appoint a remote server as the evaluator and
another as the garbler. This approach substantially diminishes
the communication complexity during the inference phase, as
communication now occurs exclusively between these two re-
mote servers. Additionally, our protocol maintains the security
of userâ€™s input even in the event of two remote servers being
compromised, because of the gateway serverâ€™s contribution to
the masking term during the setup phase. Last but not the
least, we design a transition from user-server interaction to
server-server interaction to ensure no information leakage in
this process.

VII. INFORMATION LEAKAGE ANALYSIS

In this section, we show the protocol described in Section VI
achieves the privacy goals described in Section V-A under a
passive-adversary model. Based on Composition Theorem for
semi-honest model (Theorem 7.3.3 in [36]), by proving the
security of the protocol in each phase, the security of the entire
protocol is proven.

We prove the security of the preprocessing and inference
phase following the simulation paradigm [37]. According to
the simulation paradigm, a protocol
is secure if whatever
can be computed by a party involved in the protocol can be
computed given only the input and the output of the party. So
the security can be modeled by defining a simulator that can
generate the view of the party during the procedure given the
input and the output. If the view of the party can be simulated
based on the input and the output only and is computationally
indistinguishable from the real view of the party, it implies the
party only learns what can be computed given the input and
the output, so the protocol is secure.

A. Setup phase

The setup phase is independent of the rest of the protocol.
For a given user and the servers, it has to be run only once.
The protocol used in the setup phase is a composition of
HE.KeyGen(.) and MPHE.DKeyGen(.).

In Mouchet et al. [30], it shows that the protocol in the
setup phase can securely and correctly generate a valid plain
BFV key pair. Provided with valid plain BFV key pair,
HE.Enc and MPHE.Enc can output valid BFV ciphertext,
which guarantees the semantic security of HE and MPHE
schemes described in Proposition VII.1 and Proposition VII.2.
The semantic security of HE and MPHE schemes provides the
security basis for the following two phases.

Proposition VII.1 (HE semantic security). For any two
messages m1, m2, no adversary has an advantage (better
in distinguishing between distributions
than 1/2 chance)
HE.Enc(pk, m1) and HE.Enc(pk, m2).

Proposition VII.2 (MPHE-based MPC semantic security).
For any subsets of at most colluded N âˆ’ 1 clients, for any
two messages m1 and m2, no adversary has an advantage
(better than 1/2 chance) in distinguishing between distribu-
tions MPHE.Enc(cpk, m1) and MPHE.Enc(cpk,m2).

B. Preprocessing and Inference Phase

In this section, we prove the privacy goals in Section V-A
are achieved in the preprocessing and inference phase follow-
ing the simulation paradigm [37].

We can prove the security of the preprocessing and inference
phase by 1) providing the real view of the adversary for the
case when the user or two servers are corrupted 2) describing
simulators for cases where two servers or the user are cor-
rupted 3) comparing each term in the view of the adversary
and proving the indistinguishability. We have three privacy
goals that are to preserve the privacy of 1) the userâ€™s input
2) the intermediate prediction result 3) the complete model

parameters. Intuitively, by distributing the model parameters,
the honest serverâ€™s partial model parameters are protected
thus the adversary cannot obtain the complete model. The
userâ€™s input and the intermediate prediction result are protected
by the randomness. To prove they are fully secure, we can
determine the indistinguishability of each element in the view
separately. Note Composition Theorem [36] can be applied to
the sequential compositions of arbitrary protocols involving
multiple parties. Based on Composition Theorem [36], the
security of the protocols for two phases is proven when the
composing sub-protocols are secure. The security proof of
cryptographic sub-protocols (section III-B) are provided in
[30][38][39] assuming the passive adversary model.

We name the protocols of two phases as PRE and INF and

define the corresponding ideal functionality as

fpre(pk0, cpk, {Ci}L
= {{shareU
i }l
finf (x1, {shareU
i }l
= {{mski}L
i=1}

i=1, {Fi}l
i=1, {shareA
i=1, {shareA

i=1, {Fj
i }L
i }L

i }i=L
i=l+1, { ËœCi}L
i=l+1, { ËœCi}L

i=l+1,j=2,3)
i=1}
i=1)

(1)

(2)

i }L

i ) âˆ’ s2

i = (F2

i=1, {shareA

i=l+1, {mski = xi âˆ’ ri}L

i = Firi âˆ’ si}l
i âˆ’ s3

where {shareU
i + F3
i +
i + r3
r2
i=1. Next we we
discuss the cases where server A and B are corrupted and the
user is corrupted. The proofs for other cases, wherein either
servers B and C or servers A and C are corrupted, can be
readily extended based on the methodology outlined in the
following proof.

i )(r1

a) Server A, B corrupted: The real view vAB of the

adversary corrupting server A and B includes:
1) Ciphertexts set ctSAB = {{ctri}l+1

i=1, {ctr2
, ctr3
}L
i=l+1}
, cts2
2) The masked input {mski = xi âˆ’ ri}l+1
i=1, {mski = xi âˆ’

}L
i=l+2, {ctshareA

}L
i=l+2,

{ctF 2

, ctF 3

, cts2

i

i

i

i

i

i

i

i }L+1
r3
l+2

{l + 1, ..., L}

3) The secret shares set shareA

i = (F2

i +F3

i )riâˆ’s2

i âˆ’s3

i , i âˆˆ

4) Garbled circuit { ËœCi}L

i=1 and labels {labeli}L

i=l+1

We define a simulator SAB that simulates the view of an
adversary corrupting server A and B. For a given value x, we
denote the simulated equivalent by Ëœx and the encryption of
it by ctx. SAB is given pk0, cpk, FA, {F2
and proceeds as follows:

i=l+1, (qi, wi)L

i }L

i=1

1) SAB chooses a uniform random tape for server A and

B.

2) In the preprocessing phase:

a) SAB,

the

user,

as
HE.Enc(pk0, Ëœri)}l+1
i=1
A where Ëœri â† Zqi
evaluated ciphertext from server A.

{ Ëœctri
=
to server
q . Then SAB receives the

and sends

computes

it

b) With SAB as the evaluator of the garbled circuits
for ith, i âˆˆ {1, ..., l} non-linear layer, SAB receives
ËœCi from server A and labels corresponding to
random input generated by SAB.

c) Server B computes and sends the ciphertexts

i

ctF 2
ctr2
cts2

i

i

= MPHE.Enc(cpk, F2
i )
= MPHE.Enc(cpk, r2
i )
= MPHE.Enc(cpk, s2
i )

to server A.

q , Ëœs3

i â† Zwi
q

d) SAB, as server C, sets ËœF3

i = 0, then generates
i â† Zqi
Ëœr3
and encrypts them with cpk;
During distribute decryption, server B receives the
evaluated ciphertext from server A and server A
i ) âˆ’
computes (cid:103)share
i âˆ’ Ëœs3
s2
i
3) In the inference phase:

A
i = (F2

i + ËœF3

i + Ëœr3

i + r2

i )(r1

a) Preamble: SAB, as the user, sends âˆ’Ëœr1 to server A
to evaluate the first linear layer. Then SAB receives
the corresponding GC label.

b) SAB evaluates ËœCi to obtain the output of garbled

1) The masked input {mski = xi âˆ’ ri âˆ’ di}l
2) The additive share {shareU
i = Firi âˆ’ si}l
3) Garbled circuit { ËœCi}l
We define a simulator SU that simulates the view of an
adversary corrupting the user. SU is given x1, pk0, cpk and
proceeds as follows:

i=1
i=1 and labels {labeli}l

i=1

i=1

1) SU chooses a uniform random tape for the user.
2) In the preprocessing phase:

a) SU ,

as

server A,

HE.Enc(pk0, ri)}l+1
ËœFi set
to 0,
{ctsi = HE.Enc(pk0, âˆ’Ëœsi)}l+1
randomly chosen Ëœsi from Zwi
q .

{ctri
receives
i=1 with ri â† Zqi

=
q . With
receives the evaluated
i=1 from SU for a

the user

b) With SU acting as the garbler of the garbled
circuits for ith, i âˆˆ {1, ..., l} non-linear layer, the
user receives ËœCi from SU and labels corresponding
to ri and Ëœsi. SU sets the output of the circuit to be
a random value.

circuits and sends it to server A.

3) In the inference phase:

c) Transition: SAB, as server C, receives the output

of first l layers

d) SAB obtains labels corresponding to Ëœs3

i+1
from server B, computes the output of garbled
circuits and sends it to server B

i and Ëœr3

Theorem VII.1. The view simulated by SAB is computaion-
ally indistinguishable from the real view vAB when the adver-
sary is corrupting server A and B.

Proof. We observe that the PRE and INF protocol can be
privately reducible to the HE, MPHE, GC and other protocols.
the secuirty of PRE and INF protocol follow
Therefore,
from the standalone security of each protocol by applying
Composition Theorem for semi-honest model [36]. The in-
distinguishability of ciphertext is guaranteed by the semantic
security (Proposition VII.1 and Proposition VII.2) of protocol
HE and MPHE, and the indistinguishability of garbled circuits
with labels is guaranteed by the security property of protocol
GC [38]. We only need to show the indistinguishability of
the masked input and the the secret shares,
then we can
prove that PRE and INF preserve their security. Due to
using different random values which share identical distribu-
c
tion hence are statistically equivalent, we get { (cid:103)mski}L
â‰¡
c
â‰¡ {shareA
{mski}L

i=1, { (cid:103)share

A
i }L

i=l+1.

i }L

i=l+1

i=1

The arguments above yields the following security property.

Proposition VII.3. SECO introduced in Section VI securely
realizes fpre and finf in the presence of semi-honest adver-
sary controlling server A and B.

1) The user corrupted: We prove that the simulated view
and the real view are computationally indistinguishable, thus
information such as the model parameters which is beyond the
view cannot be computed if the adversary corrupts the user.
The real view vU of the adversary corrupting the user

a) Preamble: SU , as server A, receives x1 âˆ’ r1 from

the user

b) SU , as server A, sets the Fi = 0 evaluates to obtain
Ëœsi and sends the corresponding simulated labels to
the user.

c) The user evaluates ËœCi

to obtain the output of
garbled circuits which is set randomly, then sends
it to SU .

Theorem VII.2. The view simulated by SU is computaionally
indistinguishable from the real view vU when the adversary is
corrupting the user.

Proof. Similar to the proof of Theorem VII.1,
the views
are computationally indistinguishable based on the security
properties of HE, MPHE, GC and the use of randomness that
are statistically equivalent.

The arguments above yields the following security property.

Proposition VII.4. SECO introduced in Section VI securely
realizes fpre and finf in the presence of semi-honest adver-
sary controlling the user.

VIII. EXPERIMENTS

In this section, we experimentally evaluate the performance
of SECO and present our experimental results comparing
SECO and other protocols. Currently, SECO supports the
deployment of CNN models.

A. Implementation

Our implementation is based on SEAL library [40] and
DELPHIâ€™s open source code 1. We first implemented the oper-
ations for multiparty key-generation and distribute-decryption
for BFV scheme [30] in SEAL. Then we modified DEL-
PHIâ€™s implementation to support the collaborative inference
involving multiple parties as described in Section VI. For

includes:

1https://github.com/mc2-project/delphi

convolutional functions, we employ modulus-switching to
reduce the ciphertext size as in Cryptflow2 [41]. We use the
same BFV security parameters as DELPHI uses, with 8192
as the degree of polynomial modulus and 2061584302081 as
plaintext modulus.

(a) ResNet32 online time

(b) ResNet32 preprocessing time

Fig. 4. Comparison of SECO and DELPHI on execution time of ResNet32

(a) ResNet32 online communication

(b) ResNet32 preproccessing communication

Fig. 5. Comparison of SECO and DELPHI on communication cost of
ResNet32

B. Setup

We run our benchmarks in the WLAN setting with four
instances in Australia or North America. All the instances
have Intel Xeon Processor running at 2.3 GHz with 32GB of
RAM. Each experiment is conducted 5 times, and the results
presented are the average of these runs.

C. Performance

1) Compare with HE-MPC-based Protocols: We exper-
imentally evaluate SECO in terms of execution time and
communication cost for preprocessing and inference phase
with the deployed model split at different layers. We present
the comparison results of SECO, DELPHI [8], and DELPHI-
3. DELPHI-3 is a straightforward extension of DELPHI to
3PC setting. This extension employs MPHE for processing
linear functions, while utilizing Garbled Circuits (GC) for non-
linear operations. A key distinction between DELPHI-3 and
SECO, lies in the allocation of roles within the GC scheme.
In SECO, two remote servers are designated as the garbler and
the evaluator in the GC process. In DELPHI-3, the gateway
server assumes the role of the evaluator, while a remote server
functions as the garbler. This will lead to different performance
of SECO and DELPHI-3 in only online inference phase. We
evaluate three schemes on ResNet32 [42] (with 62 layers in
total).

a) Userâ€™s experience: Figure 4(a) shows the comparison
of the online execution time. As illustrated in the figure, the
blue bars indicate the duration for which the user must remain
connected and actively process the computation while the light
blue bars represent the time required to process the model
on remote servers. The total height of the bars in the figure
represents the userâ€™s waiting time, spanning from the start of
the query to the receipt of the prediction result. We can tell
that the fewer layers deployed on gateway server A, the less
execution time of SECO in the preprocessing phase. When all
the layers of the model are on server A, SECO is reduced
to DELPHI and only the user and server A are involved in
the computation. When the number of layers on server A is
reduced to two, SECO offers the most efficient experience in
terms of both the shortest waiting and participation time for the
user comparing to DELPHI, thereby potentially minimizing
the userâ€™s computational burden. We note that SECO can
operate on a device with just 2 GB of memory as the user
device (with less than 10 layers of ResNet32 on the gate-
way server), whereas DELPHI cannot support such a device,
making meaningful comparison impossible. This capability
allows SECO to utilize lightweight devices, such as the smart
watch, as user devices. Depending on the numbers of layers on
server A, SECOâ€™s results are between 2.6 Ã— âˆ’1Ã— faster than
DELPHI in terms of userâ€™s waiting time. Accordingly, SECOâ€™s
efficiency ranges from 9.9Ã—âˆ’1Ã— faster than DELPHI in terms
of userâ€™s participation time.

Figure 4(b) shows the comparison of the preprocessing
execution time, revealing a similar trend as the observation
in Figure 4(a). Depending on the numbers of layers on server
A, SECOâ€™s results are between 11 Ã— âˆ’1Ã— faster than DELPHI
in terms of userâ€™s preprocessing time. We note that SECOâ€™s
preprocessing only involves the preprocessing of FA. The
three server pre-compute the secret shares for FBC before
the user appears in the system.

As illustrated in Figure 5(a) and Figure 5(b), SECO demon-
strates up to 18.5Ã— more efficient compared to DELPHI in

TABLE II
COMPARISON OF EXECUTION TIME AND COMMUNICATION COST

MiniONN

LeNet

Time (s)

Comm. cost (MB)

Time (s)

Comm. cost

SecureNN
Falcon
SECO

183.493
8.426
4.776

177.264
1.097
50.479

-
9.303
4.862

-
1.611
58.888

communication cost for the user in protocols including SECO,
Falcon [22], and SecureNN [21]. Although there is only a
one-way transmission from user to servers, due to the use of
replicated secret shares, the user in Falcon needs to duplicates
each of the three input shares, and the user must transmit
two distinct shares to the respective server. This process leads
to a communication cost that is 6Ã— greater compared to that
in SECO. SecureNN uses a 2-out-of-2 secret sharing scheme
between two servers, and the user needs to deliver each of two
shares to the respective servers. It differs from the 2-out-of-
2 secret sharing used between a user and a server in SECO.
This process results in the communication cost 2Ã— greater
compared to SECO. Furthermore, we assess the execution
time starting from when the user transmits the input until the
user receives the prediction result. In Table II, we evaluate
3 protocols on MiniONN and LeNet. The outperformance of
SECO is attributed to the online inference only involving two
(remote) servers while other protocols are executed between
three servers. Although SECO is faster than other MPC-based
protocols, it incurs a communication cost between servers that
is 36 to 48 times higher than that of Falcon. We remind that
SECO operates under a different system and threat model.
SECO can protect the userâ€™s input even when the adversary
corrupts two of the three servers while other protocols assume
non-collusion between servers. The increase in communication
cost can be justified by SECOâ€™s emphasis on enhancing the
systemâ€™s robustness and trustworthiness for the user.

Fig. 7. Userâ€™s communication cost comparison

IX. CONCLUSION

In this paper, we design and implement SECO, a novel
hybrid HE-MPC-based secure inference protocol with model
splitting in a multi-server hierarchy setting. SECO ensures

(a) ResNet32 total online execution time

(b) ResNet32 total online communication cost

Fig. 6. Comparison of SECO and DELPHI-3 on execution time and
communication cost of ResNet32

is up to 16.6Ã— more efficient

terms of the userâ€™s online communication cost, additionally,
it
than DELPHI regarding
the userâ€™s preprocessing communication cost. Even though
SECOâ€™s total communication cost
in the online inference
phase is higher than DELPHIâ€™s, SECO reduces the userâ€™s
cost. Figure 5(a) shows that SECO can provide a tradeoff in
communication load between user and server nodes, which
might be desirable to service provider.

b) Effect of schemes with different assignments of servers
in GC: Figure 6(a) and Figure 6(b) depict the online per-
formance of SECO, DELPHI, and DELPHI-3. We can tell
from figures, the time and the cost for processing FA are
the same for SECO and DELPHI-3 as the 2PC protocol in
both cases is derived from DELPHI. However, the time and
cost for processing FBC are significantly reduced in SECO.
The inefficiency in DELPHI-3 arises because the evaluator of
the garbled circuit obtains labels for server Aâ€™s share during
FBC pre-computation, making server Aâ€™s participation in the
inference phase unnecessary. In contrast, SECO designates
server C as the evaluator, involving only servers B and C
in the inference phase. Our approach streamlines the process,
avoiding the need for three-server involvement as in DELPHI-
3.

2) Compare with MPC-based protocols: In this section, we
compare SECO with pure MPC-based protocols. To make a
fair comparison, we deploy all the layers of the model on
remote servers in SECO. So the user can send the masked
input and receive the prediction result without further inter-
action like in pure MPC-based protocols. Figure 7 shows the

1022344658Number of layers stored on server A0255075100125150175200Execution time (s)DELPHISECO FASECO FBCDELPHI-3 FADELPHI-3 FBC1022344658Number of layers stored on server A0.00.20.40.60.81.0Communication cost (GB)DELPHISECO FASECO FBCDELPHI-3 FADELPHI-3 FBCthe confidentiality of the input data withstanding passive
adversaries corrupting up to 2 servers, and also protects the
model parameters from the user. Furthermore, SECO hides
more information about the model architecture than other HE-
MPC-based protocols and pure MPC-based protocols. In the
experiments, SECO is shown to minimize the user deviceâ€™s
obligation in computation and communication, making it ap-
plicable to devices with limited resources.

REFERENCES

[1] J. Fan and F. Vercauteren, â€œSomewhat practical fully homomorphic
encryption,â€ IACR Cryptol. ePrint Arch., vol. 2012, p. 144, 2012.
[2] A. C.-C. Yao, â€œHow to generate and exchange secrets (extended ab-

stract),â€ in FOCS, 1986.

[3] R. Gilad-Bachrach, N. Dowlin, K. Laine, K. Lauter, M. Naehrig, and
J. Wernsing, â€œCryptonets: Applying neural networks to encrypted data
with high throughput and accuracy,â€ in International conference on
machine learning, pp. 201â€“210, PMLR, 2016.

[4] E. Hesamifard, H. Takabi, and M. Ghasemi, â€œCryptodl: Deep neural

networks over encrypted data,â€ 2017.

[5] R. Dathathri, O. Saarikivi, H. Chen, K. Laine, K. Lauter, S. Maleki,
M. Musuvathi, and T. Mytkowicz, â€œChet: an optimizing compiler for
fully-homomorphic neural-network inferencing,â€ in Proceedings of the
40th ACM SIGPLAN Conference on Programming Language Design and
Implementation, pp. 142â€“156, 2019.

[6] A. Sanyal, M. J. Kusner, A. GascÂ´on, and V. Kanade, â€œTapas: Tricks to

accelerate (encrypted) prediction as a service,â€ 2018.

[7] C. Juvekar, V. Vaikuntanathan, and A. Chandrakasan, â€œGazelle: A low
latency framework for secure neural network inference,â€ 01 2018.
[8] P. Mishra, R. T. Lehmkuhl, A. Srinivasan, W. Zheng, and R. A. Popa,
â€œDelphi: A cryptographic inference service for neural networks,â€ in
IACR Cryptol. ePrint Arch., 2020.

[9] C. Gentry, â€œFully homomorphic encryption using ideal

lattices,â€ in
Proceedings of the forty-first annual ACM symposium on Theory of
computing, pp. 169â€“178, 2009.

[10] V. Nikolaenko, U. Weinsberg, S. Ioannidis, M. Joye, D. Boneh, and
N. Taft, â€œPrivacy-preserving ridge regression on hundreds of millions of
records,â€ in 2013 IEEE Symposium on Security and Privacy, pp. 334â€“
348, 2013.

[11] D. Wu and J. Haven, â€œUsing homomorphic encryption for large scale
statistical analysis,â€ FHE-SI-Report, Univ. Stanford, Tech. Rep. TR-
dwu4, 2012.

[12] R. Bost, R. A. Popa, S. Tu, and S. Goldwasser, â€œMachine learning

classification over encrypted data,â€ Cryptology ePrint Archive, 2014.

[13] J. W. Bos, K. Lauter, and M. Naehrig, â€œPrivate predictive analysis on
encrypted medical data,â€ Journal of biomedical informatics, vol. 50,
pp. 234â€“243, 2014.

[14] T. Graepel, K. Lauter, and M. Naehrig, â€œMl confidential: Machine
learning on encrypted data,â€ in International Conference on Information
Security and Cryptology, pp. 1â€“21, Springer, 2012.

[15] I. Chillotti, N. Gama, M. Georgieva, and M. Izabachene, â€œFaster fully
homomorphic encryption: Bootstrapping in less than 0.1 seconds,â€ in
international conference on the theory and application of cryptology
and information security, pp. 3â€“33, Springer, 2016.

[16] F. Boemer, Y. Lao, R. Cammarota, and C. Wierzynski, â€œngraph-he: A
graph compiler for deep learning on homomorphically encrypted data,â€
2018.

[17] C. Boura, N. Gama, and M. Georgieva, â€œChimera: a unified framework
for b/fv, tfhe and heaan fully homomorphic encryption and predictions
for deep learning,â€ IACR Cryptol. ePrint Arch., vol. 2018, p. 758, 2018.
[18] B. Reagen, W.-S. Choi, Y. Ko, V. T. Lee, H.-H. S. Lee, G.-Y. Wei,
and D. Brooks, â€œCheetah: Optimizing and accelerating homomorphic
encryption for private inference,â€ in 2021 IEEE International Symposium
on High-Performance Computer Architecture (HPCA), pp. 26â€“39, 2021.
[19] D. Demmler, T. Schneider, and M. Zohner, â€œAby-a framework for
efficient mixed-protocol secure two-party computation.,â€ in NDSS, 2015.
[20] P. Mohassel and P. Rindal, â€œAby3: A mixed protocol framework for
machine learning,â€ in Proceedings of the 2018 ACM SIGSAC conference
on computer and communications security, pp. 35â€“52, 2018.

[21] S. Wagh, D. Gupta, and N. Chandran, â€œSecurenn: 3-party secure com-
putation for neural network training.,â€ Proc. Priv. Enhancing Technol.,
vol. 2019, no. 3, pp. 26â€“49, 2019.

[22] S. Wagh, S. Tople, F. Benhamouda, E. Kushilevitz, P. Mittal, and
T. Rabin, â€œFalcon: Honest-majority maliciously secure framework for
private deep learning,â€ arXiv preprint arXiv:2004.02229, 2020.

[23] F. Boemer, R. Cammarota, D. Demmler, T. Schneider, and H. Yalame,
â€œMp2ml: A mixed-protocol machine learning framework for private
inference,â€ in Proceedings of the 2020 Workshop on Privacy-Preserving
Machine Learning in Practice, PPMLPâ€™20, (New York, NY, USA),
p. 43â€“45, Association for Computing Machinery, 2020.

[24] J. H. Cheon, A. Kim, M. Kim, and Y. Song, â€œHomomorphic encryption
for arithmetic of approximate numbers,â€ in International conference
on the theory and application of cryptology and information security,
pp. 409â€“437, Springer, 2017.

[25] C. Thapa, M. A. P. Chamikara, S. Camtepe, and L. Sun, â€œSplitfed: When

federated learning meets split learning,â€ 2022.

[26] G.-L. Pereteanu, A. Alansary, and J. Passerat-Palmbach, â€œSplit he: Fast
secure inference combining split learning and homomorphic encryption,â€
arXiv preprint arXiv:2202.13351, 2022.

[27] T. Khan, K. Nguyen, and A. Michalas, â€œSplit ways: Privacy-preserving

training of encrypted data using split learning,â€ 2023.

[28] P. Vepakomma, O. Gupta, T. Swedish, and R. Raskar, â€œSplit learning
for health: Distributed deep learning without sharing raw patient data,â€
arXiv preprint arXiv:1812.00564, 2018.

[29] O. Gupta and R. Raskar, â€œDistributed learning of deep neural network
over multiple agents,â€ Journal of Network and Computer Applications,
vol. 116, pp. 1â€“8, 2018.

[30] C. Mouchet, J. Troncoso-Pastoriza, J.-P. Bossuat, and J.-P. Hubaux,
â€œMultiparty homomorphic encryption from ring-learning-with-errors,â€
Proceedings on Privacy Enhancing Technologies, vol. 4, pp. 291â€“311,
2021.

[31] M. O. Rabin, â€œHow to exchange secrets with oblivious transfer,â€ IACR

Cryptol. ePrint Arch., vol. 2005, p. 187, 2005.

[32] S. Even, O. Goldreich, and A. Lempel, â€œA randomized protocol for

signing contracts.,â€ vol. 28, pp. 205â€“210, 01 1982.

[33] M. Bellare, T. Hoang, and P. Rogaway, â€œFoundations of garbled circuits,â€

pp. 784â€“796, 10 2012.

[34] M. Bellare, V. T. Hoang, S. Keelveedhi, and P. Rogaway, â€œEfficient
garbling from a fixed-key blockcipher,â€ in 2013 IEEE Symposium on
Security and Privacy, pp. 478â€“492, 2013.

[35] Z. He, T. Zhang, and R. B. Lee, â€œModel inversion attacks against
collaborative inference,â€ in Proceedings of the 35th Annual Computer
Security Applications Conference, ACSAC â€™19, (New York, NY, USA),
p. 148â€“162, Association for Computing Machinery, 2019.

[36] O. Goldreich, â€œFoundations of cryptography. ii: Basic applications,â€

vol. 2, 05 2004.

[37] Y. Lindell, â€œHow to simulate itâ€“a tutorial on the simulation proof
technique,â€ Tutorials on the Foundations of Cryptography, pp. 277â€“346,
2017.

[38] Y. Lindell and B. Pinkas, â€œA proof of security of yaoâ€™s protocol for
two-party computation,â€ Journal of Cryptology, vol. 22, pp. 161â€“188,
04 2009.

[39] M. O. Rabin, â€œHow to exchange secrets with oblivious transfer,â€ 2005.
Harvard University Technical Report 81 talr@watson.ibm.com 12955
received 21 Jun 2005.

[40] â€œMicrosoft SEAL (release 3.6).â€ https://github.com/Microsoft/SEAL,

Nov. 2020. Microsoft Research, Redmond, WA.

[41] D. Rathee, M. Rathee, N. Kumar, N. Chandran, D. Gupta, A. Rastogi,
and R. Sharma, â€œCrypTFlow2: Practical 2-party secure inference,â€ in
Proceedings of the 2020 ACM SIGSAC Conference on Computer and
Communications Security, ACM, oct 2020.

[42] K. He, X. Zhang, S. Ren, and J. Sun, â€œDeep residual learning for image
recognition,â€ in Proceedings of the IEEE conference on computer vision
and pattern recognition, pp. 770â€“778, 2016.

[43] J. Liu, M. Juuti, Y. Lu, and N. Asokan, â€œOblivious neural network
predictions via minionn transformations,â€ in Proceedings of the 2017
ACM SIGSAC conference on computer and communications security,
pp. 619â€“631, 2017.

[44] Y. Lecun, L. Bottou, Y. Bengio, and P. Haffner, â€œGradient-based learning
applied to document recognition,â€ Proceedings of the IEEE, vol. 86,
no. 11, pp. 2278â€“2324, 1998.

APPENDIX A
NOTATION

Table III provides the summary of

the symbols used

throughout this work.

APPENDIX B
SECURITY PROOF

We provide the security proof for other cases when server

B and C are corrupted or server A and C are corrupted.

a) Server B, C corrupted: The real view vBC of the

adversary corrupting server B and C includes:

i

, ctF 3

{ctF 2

1) Ciphertexts set ctSBC = {{ctr2
, cts2

}L
i=l+2,
}L
}L
i=l+1}
i=l+2, {ctshareA
2) The masked input of mski = xi âˆ’ r1
3) Garbled circuit { ËœCi}L
by Server B and C

i=l+1 and {labeli}L

, ctr3

, cts2

i

i

i

i

i

i

i , i âˆˆ {l + 2, ..., L}
i=l+1 obtained

We define a real-world simulator SBC that simulates the
view of an adversary corrupting server B and C. SBC is
i=l+1, pk0, cpk, {(qi, wi)}L
given {F2
i=l+1, mskl+1 and
proceeds as follows:

i , F3

i }L

1) SBC chooses a uniform random tape for server B and

C.

2) In the preprocessing phase:

a) SBC,

as
MPHE.Enc(cpk, Fj
MPHE.Enc(cpk, rj
server B and C.
b) SBC generates Ëœr1
i + r2
i + F2

i )(Ëœr1

(F3

receives

server A,
i ),
i ), MPHE.Enc(cpk, sj
i )

ciphertexts

from

i â† Zqi
i + r3

A
i =
Q and computes (cid:103)share
i âˆ’ s2
i ) âˆ’ s3
i

c) Server B sends the garbled circuit ËœCi and labels
for inputs from server B to server C; SBC obtains
the labels from server B and forwards it to server
C

3) In the inference phase:

a) Transition: SBC generates a random value as the
output of the first l layers mskl+1 and sends it to
server B and C

Theorem B.1. The view simulated by SBC is computaionally
indistinguishable from the real view vBC when the adversary
corrupting server B and C.

Proof. Similar to the proof of Theorem VII.1,
the views
are computationally indistinguishable based on the security
properties of HE, MPHE, GC, and the use of randomness
that are statistically equivalent.

The arguments above yields the following security property.

Proposition B.1. SECO introduced in Section VI securely re-
alizes fpre and finf in the presence of semi-honest adversary
controlling server B and C.

2) The masked input of the ith, i âˆˆ {l + 2, ..., L} layer

mski = xi âˆ’ r2
i

3) The additive secret shares set shareA
i , i âˆˆ {l + 1, ..., L}

i âˆ’ s3
s2

i = (F2

i + F3

i )ri âˆ’

4) Garbled circuit { ËœCi}L

i=1 and {labeli}L

i=l+1 for garbled

circuits

We define a real-world simulator SAC that simulates the view
of an adversary corrupting server A and C. SAC is given
{F3

i , (qi, wi)}L
1) SAC chooses a uniform random tape for server A and

i=l+1, FA, pk0, cpk and proceeds as follows:

C.

2) In the preprocessing phase:

a) SAC, as the user, computes HE.Enc(pk0, Ëœri), i âˆˆ
{1, ..., l + 1} to server A where Ëœri is randomly
chosen from Zqi
Q . Then SAC receives the evaluated
ciphertext from server A.

b) With SAC as the evaluator of the garbled circuits
for ith, i âˆˆ {1, ..., l} non-linear layer, SAC receives
ËœCi, i âˆˆ {1, ..., l} from server A and labels corre-
sponding to random input generated by SAC.

i â† Zwi

c) SAC, as server B, sets ËœF2
Q , Ëœs2

i = 0, then generates
i â† Zqi
Ëœr2
Q and encrypts them respec-
tively with cpk; For processing distribute decryp-
tion, server C receives the evaluated ciphertext
A
i = (F3
i +
from server A and (cid:103)share
i ) âˆ’ s3
r1
i from SAB

i + ËœF2

i âˆ’ Ëœs2

i + Ëœr2

i )(r3

d) SAC, as server B, runs the simulator for garbled
circuits and generates ËœCi, i âˆˆ {l + 1, ..., L}, then
sends labels corresponding to Ëœr2

i to server C

3) In the inference phase:

a) Preamble: SAC sends âˆ’Ëœr1 to server A to evaluate

the first linear layer.

b) SAC, as the user, obtains labels from server A
c) SAC, as the user, sends a random value as the

output of garbled circuits back to server A.

d) Transition: SAC, as server B, receives the output

of the first l layers

e) SAC, as server B, sends labels corresponding to Ëœs2
i

to server C

f) SAC receives the output of garbled circuits from

server C

Theorem B.2. The view simulated by SAC is computaionally
indistinguishable from the real view vAC when the adversary
corrupting server A and C.

Proof. Similar to the proof of Theorem VII.1,
the views
are computationally indistinguishable based on the security
properties of HE, MPHE, GC, and the use of randomness
that are statistically equivalent.

b) Server A, C corrupted: The real view vAC of the

The arguments above yields the following security property.

adversary corrupting server A and C includes:
1) Ciphertexts set ctSAC = {{ctri}l+1
, ctr3
i=1, {ctr2
}L
i=l+1}

}L
i=l+2, {ctshareA

{ctF 2

, ctF 3

, cts2

, cts2

i

i

i

i

i

i

i

}L
i=l+2,

Proposition B.2. SECO introduced in Section VI securely re-
alizes fpre and finf in the presence of semi-honest adversary
controlling server A and C.

TABLE III
NOTATION SUMMARY

Description

[âˆ’ q

Party index (0 for the user, 1 for server A, 2 for server B, 3 for server C)
2 , q
2 )
Plaintext space for HE scheme
Ciphertext space for HE scheme
Total number of layers of the model
The number of layers stored on server A
Input size of ith layer
Output size of ith layer
The partial model on server A
The partial model on server B and C
Model parameter of the ith layer
Model parameter of the ith layer on Party j
The input of the modelâ€™s ith layer
The prediction result
Randomness masking the input of ith layer
Randomness masking the output of ith layer
Key pair generated by party j
Common public key
Ciphertext of message x
Circuit for computing the ith ReLU layer
Garbled circuit correspongind to Ci
Garbled circuit input labels corresponding to value x

Symbol

j
Zq
Rt
Rq
L
l
qi
wi
FA
FBC
Fi
Fj
i
xi
Ë†y
ri
si
(skj , pkj )
cpk
ctx
Ci
ËœCi
labelx

APPENDIX C
DELPHI-3

encrypted domain. Server A can evaluate the garbled circuit
when collecting all labels for input wires of ËœCi. Note the
inefficiency of this method is that despite three servers holding
the respective additive shares of the real prediction result, the
evaluator of the garbled circuit already obtains the labels for
server Aâ€™s share during the pre-computation for FBC. Thus
server A does not need to involve in the inference phase of
FBC. We observe this inefficiency and set server C as the
evaluator in SECO instead.

APPENDIX D
SETUP PHASE IN SECO

The setup phase in SECO includes the MPHE key genera-
tion and the preparation for FBC. This phase involves three
servers. In Table IV and Table V, we provide the execution
time and communication cost for the setup phase.

APPENDIX E
STRUCTURES OF NEURAL NETWORKS

a) MiniONN: This is a 4 layer network with 2 convolu-
tional and 2 fully-connected layers selected from prior work
MiniONN [43]. The structure is provided in Table VI. It has
around 10,500 parameters in total.

b) LeNet: This network, proposed by LeCun et al. [44]
contains 2 convolutional layers and 2 fully connected layers
with about 431K parameters. Table VII shows the structure.

APPENDIX F
PSEUDOCODE

DELPHI-3 is a 3PC protocol directly expanded from DEL-
PHI. DELPHI-3 sets server B as the garbler and server A as
the evaluator for GCs.

a) Preprocessing for FBC: The preprocessing of linear
layers is the same with SECO as described in Algorithm 8. The
preprocessing of ReLU is as follows: with server B as the gar-
bler, server A as the evaluator, and server C providing input as
the third party, server B first prepares the garbled circuit ËœCi and
labels by running GC.Garble(Params, Ci) where Params is
the security parameters and Ci is described in Algorithm 9 in
Appendix F. To transmit the labels corresponding to actual
input values, server B sends the labels of the input value
provided by itself to server A through a public channel. For
input values from server A and C, server A and C first obtain
the actual labels from server B via OT. Then server A collects
the labels obtained by server C through a public channel.

b) Online-inference for FBC: The inference of FBC
involves the participation of server A, B, and C. At
the
beginning of the inference for ith layer i âˆˆ {l+1, ..., L}, server
B and C hold xi âˆ’ ri where ri is solely contributed by the
user when i = l + 1, and is contributed by server A, B and C
for linear other layers of FBC. Server A, B and C collaborate
to do inference on ith layer i âˆˆ {l + 1, ..., L}. First server
B and C will compute Fj
i , resulting in three
servers holding three additive shares of the real prediction
result for the current layer (F2
i )xi. The garbled circuit
ËœCi on server A (Algorithm 9 in Appendix F) first aggregates
shares to recover (F2
i )xi, then computes ReLU of it,
finally masks the ReLU output with the randomness of the next
layer contributed by three servers. The entire process is in the

i (xi âˆ’ ri) + sj

i + F3

i + F3

TABLE IV
SETUP PHASE OF SECO ON RESNET32 (1)

Numbers of layers on server B,C

60

56

52

48

44

40

36

32

Execution time (s)
Comm. cost (GB)

290.202
21.609

271.366
19.920

250.965
18.230

233.168
16.541

215.994
14.851

192.566
13.161

175.395
11.747

162.568
10.621

TABLE V
SETUP PHASE OF SECO ON RESNET32 (2)

Numbers of layers on server B,C

28

24

20

16

12

8

4

Execution time (s)
Comm. cost (GB)

148.177
9.495

136.214
8.368

117.166
7.242

91.340
5.822

68.487
4.404

41.719
2.985

16.042
1.567

Layer
1
2
3
4
5
6
7
8
9

Layer
1
2
3
4
5
6
7
8
9

Type
Convolution
Subsampling
ReLU
Convolution
Subsampling
ReLU
Fully Connected
ReLU
Fully Connected

Input Size
28Ã—28Ã—1
24Ã—24Ã—16
1 Ã— 2304
12Ã—12Ã—16
8Ã—8Ã—16
1Ã—256
256
100
100

Output Size
24Ã—24Ã—16
12Ã—12Ã—16
1 Ã— 2304
8Ã—8Ã—50
4Ã—4Ã—16
1Ã—256
100
100
10

TABLE VI
STRUCTURE OF MINIONN

Type
Convolution
Subsampling
ReLU
Convolution
Subsampling
ReLU
Fully Connected
ReLU
Fully Connected

Input Size
28Ã—28Ã—1
24Ã—24Ã—20
1 Ã— 2880
12Ã—12Ã—20
8Ã—8Ã—50
1Ã—800
800
500
500

Output Size
24Ã—24Ã—20
12Ã—12Ã—20
1 Ã— 2880
8Ã—8Ã—50
4Ã—4Ã—50
1Ã—800
500
500
10

TABLE VII
STRUCTURE OF LENET

Details
5Ã—5 filters, stride 1
2Ã—2 average pooling, stride 2

5Ã—5 filters, stride 1
2Ã—2 average pooling, stride 2

Details
5Ã—5 filters, stride 1
2Ã—2 average pooling, stride 2

5Ã—5 filters, stride 1
2Ã—2 average pooling, stride 2

Algorithm 11 A circuit Ci that computes ReLU function of
the ith layer, i âˆˆ {1, ..., l}

Input from the user: Firi âˆ’ si, ri+1
Input from server A: Fi(xi âˆ’ ri) + si, di+1
1: Compute Fixi = Fi(xi âˆ’ ri) + si + Firi âˆ’ si
2: Compute xi+1 = ReLU (Fixi)
3: Output xi+1 âˆ’ ri+1 âˆ’ di+1

Algorithm 12 Pre-Compute the share for the ith linear layer,
i âˆˆ {1, ...l}

Inputs: (qi, wi): the input and output shape of the ith
layer; (sk0, pk0): the plain HE key pair generated by the
user
The user:

ri â† Zqi
q
Encrypt ctri = HE.Enc(pk, ri)
Transmit ctri to server A

Server A:

si â† Zwi
q
Compute HE.Enc(pk, Firi âˆ’ si) and transmit this

ciphertext to the user
The user:

Decrypt the ciphertext to obtain Firi âˆ’ si using sk0

Algorithm 13 Pre-Compute the share for the l + 1th linear
layer

Inputs: (ql+1, wl+1): the input and output shape of the
l + 1th layer; cpk: common public key;
The user:

q

rl+1 â† Zql+1
Compute ctrl+1 = MPHE.Enc(cpk, rl+1)
Transmit ctrl+1 to server A

Server B and C:
l+1 â† Zwl+1
sj
Compute MPHE.Enc(cpk, sj

q

MPHE.Enc(cpk, Fj
Transmit (ctsj

l+1) â†’ ctF j

l+1

, ctF j

l+1

l+1

) to server A

Server A:

l+1) â†’ ctsj

l+1

MPHE.Eval(ctF 2
MPHE.Eval(cts2
MPHE.Eval(MPHE.Eval(ctFl+1, ctrl+1, Lin-OP)

, Add)â†’ ctFl+1
, Add)â†’ ctsl+1

, ctF 3
, cts3

l+1

l+1

l+1

l+1

, ctsl+1, Sub) â†’ ctFl+1rl+1âˆ’sl+1
Server A, B, C:

MPHE.DisDec(ctFl+1rl+1âˆ’sl+1, {skj}jâˆˆ{1,2,3})
l+1 âˆ’ s3
l+1 + F3
Server A obtains (F2

l+1)rl+1 âˆ’ s2

l+1

Algorithm 15 Inference for the ith layer, i âˆˆ {1, ..., l}

Inputs: (Fi, xi âˆ’ri, si): held by server A; ËœCi: the garbled
circuit of Algorithm 11; label: random labels for input
wires of Algorithm 11; labelFiriâˆ’si, labelri+1, labeldi+1 :
labels tranmitted to the user
Server A:

Compute Fi(xi âˆ’ ri) + si

Server A and the user:

,

GC.Transfer(label, di, Fi(xi âˆ’ ri) + si) â†’ labeldi,

labelFi(xiâˆ’ri)+si

The user obtains labelFi(xiâˆ’ri)+si, labeldi

The user:

GC.Eval( ËœCi, labelFi(xiâˆ’ri)+si, labeldi, labelri+1,

labelFiriâˆ’si) â†’ xi+1 âˆ’ ri+1 âˆ’ di+1

Send xi+1 âˆ’ ri+1 âˆ’ di+1 to Server A

Server A:

Compute xi+1 âˆ’ ri+1

Algorithm 14 Construct Garbled Circuit for the ith activation
layer, i âˆˆ {1, ..., l}

Algorithm 16 Construct
activation layer i âˆˆ {l + 1, ..., L}

the Garbled Circuits for the ith

Inputs: Params: Garbled Circuit security parameters, Ci:
the circuit in Algorithm 11; (Firi âˆ’ si, ri+1): the pre-
computed additive share of ith layer and the randomness
for next layer held by server A ; qi: the input shape of ith
layer
Server A:

di+1 â† Zqi
q
GC.Garble(Params, Ci) â†’ ËœCi, label
Transmit ËœCi to the user

The user and server A:

GC.Transfer(label, Firi âˆ’ si) â†’ labelFiriâˆ’si
GC.Transfer(label, ri+1) â†’ labelri+1
GC.Transfer(label, di+1) â†’ labeldi+1
The user obtains labelFiriâˆ’si, labelri+1, labeldi+1

the circuit

in Algorithm 9; E1
i :

Inputs: Ci:
computed additive share held by server A; r2
randomness generated by server B
Server B:

the pre-
the
i+1:

GC.Garble(Params, Ci) â†’ ËœCi, label
Transmit ËœCi to server C

Server A and B:

GC.Transfer(label, E1
Server A obtains labelE1

i

i ) â†’ labelE1

i

transmits it to server C

Server B and C:

GC.Transfer(label, r3
Server C obtains labelr3

i+1

i+1) â†’ labelr3

i+1

