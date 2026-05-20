> **DUPLICATE - do not cite separately.**
> This file is a duplicate copy of the MEDIA / SGX-empowered edge-cloud DNN partitioning paper note.
> Canonical paper note: [../secure_inference/DNN Partitioning and Assignment for Distributed Inference in SGX Empowered Edge.md](../secure_inference/DNN%20Partitioning%20and%20Assignment%20for%20Distributed%20Inference%20in%20SGX%20Empowered%20Edge.md)
> Cite the canonical note only.

> 2024 IEEE 44th International Conference on Distributed Computing
> Systems (ICDCS)
>
> DNN Partitioning and Assignment for Distributed Inference in SGX
> Empowered Edge Cloud
>
> Yuepeng Liâˆ—, Deze ZengBâˆ—Â¶, Lin Guâ€ , Song Guoâ€¡, Albert Y. ZomayaÂ§
> âˆ—School of Computer Science, China University of Geosciences, Wuhan,
> China
>
> â€ School of Computer Science and Technology, Huazhong University of
> Science and Technology, China â€¡Department of Computing, The Hong Kong
> Polytechnic University, Hong Kong Â§School of Computer Science, The
> University of Sydney, Australia
>
> Â¶Engineering Research Center of Natural Resource Information
> Management and Digital Twin Engineering Software,
>
> Ministry of Education, Wuhan 430074, China
>
> Abstractâ€”Distributed Deep Neural Network (DNN) inference is a
> promising technology to explore the distributed resources in edge
> cloud to realize edge intelligence. Meanwhile the inherent resource
> sharing nature of edge cloud infrastructure also raises serious
> concerns on security and privacy. Software Guard Ex-tensions (SGX)
> emerges as a potential hardware-level solution but its limited secure
> memory (i.e., enclave page cache) imposes new challenges, especially
> in contrast to memory-hungry DNN models. A taskâ€™s performance will be
> severely affected when its memory footprint is beyond the enclave page
> cache size, due to expensive secure page swapping. In this case, how
> to appropriately partition a DNN model and assign the partitions to
> distributed edge servers to efficiently utilize edge resources for
> fast secure inference becomes a challenging problem. In this paper, we
> first show that this problem is NP-hard. We further propose a
> <u>ME</u>mory-aware <u>D</u>istributed <u>I</u>nference
> <u>A</u>cceleration (MEDIA) algorithm, whose guaranteed approximation
> ratio is also formally analyzed. We have implemented a prototype
> system and applied some well-known representative DNN models to
> evaluate MEDIAâ€™s performance. Through extensive experiments, we verify
> the efficiency of MEDIA by the fact that it reduces the inference time
> by 19.5%-38.1% in comparison with state-of-the-art approaches.
>
> Index Termsâ€”DNN, SGX, Distributed inference
>
> I. INTRODUCTION
>
> Edge intelligence has experienced revolutionary develop-ment during
> the past years. It is anticipated that edge intelli-gence will
> facilitate almost every aspect of our daily lives by provisioning
> various applications such as smart healthcare \[1\], autonomous
> driving \[2\], and advanced video analytics \[3\]. Deep learning,
> empowered by deep neural network (DNN), is one of the key technologies
> in edge intelligence. DNN model, albeit highly potential, is notorious
> for its extremely high resource consumption as it is both
> memory-intensive and computation-intensive. For example, the widely
> adopted DNN model GoogLeNet requires about 155.9MB memory and 1.5
> billion multiply-add operations, and VGG16 even needs 1.16GB memory
> and 19.6 billion multiply-add op-erations \[4\]. It is widely
> recognized that edge servers are relatively resource-constrained. This
> makes the situation even
>
> This research was supported by the NSF of China (No. 62172375),
> Provin-cal Key Research and Development Program of Hubei
> (No.2023BAB065). Deze Zeng (deze@cug.edu.cn) is the corresponding
> author.
>
> ! \$

Fig. 1. The enclave program overhead under different memory requirements

worse as the DNN resource requirements are usually beyond the capacity
of edge servers \[5\]. Fortunately, distributed DNN recently has emerged
as a compelling solution to tackle the contradiction between resource
supply and demand in both DNN training and inference \[6\].

Edge cloud based distributed DNN inference, by making each edge server
handle a part of inference task within its abil-ity, therefore is of
great significance to edge intelligence \[5\], \[7\], \[8\]. Much recent
effort has been devoted to optimizing the distributed DNN inference
performance in edge cloud, objective at inference acceleration \[7\],
request throughput promotion \[8\] and cost minimization \[5\]. Besides,
the security and privacy of DNN inference is another important issue
drawing growing attention, due to the resource sharing of edge cloud.
For example, a malicious tenant co-locating on the same server can
acquire sensitive data via using side-channel attacks \[9\] or injection
attacks \[10\]. Even the untrustworthy infrastructure providers may also
intentionally thwart the DNN model inference process by injecting fake
data \[11\]. In this regard, many solutions, such as homomorphic
encryption \[12\], garbled circuits \[13\], have been proposed.
Unfortunately, these cryptology based solutions are not only performance
inefficient but also with limited application scope \[14\].

Hence, Software Guard Extensions (SGX) \[15\], as a hardware-level
protection technology, has been advocated to many security-critical
applications \[16\]â€“\[19\], including intelli-gent applications with DNN
inference \[14\], \[20\]. SGX builds a special secure memory region
called Enclave Page Cache (EPC), in which the loaded code and data are
protected from other untrusted programs (including the operation system)
during execution. However, the secure memory capacity, i.e.,

2575-8411/24/\$31.00 Â©2024 IEEE 635 DOI 10.1109/ICDCS60910.2024.00065

> Authorized licensed use limited to: Universiteit van Amsterdam.
> Downloaded on May 19,2026 at 12:06:17 UTC from IEEE Xplore.
> Restrictions apply.

EPC size, of SGX is limited to 128MB in the latest prod-ucts \[15\].
Once the memory usage of a task exceeds the EPC size, it will suffer
from critical performance degrada-tion. We conducted a preliminary
experiment to assess such degradation by gradually increasing the memory
requirement of a character counter application. We sent different sizes
of character strings into EPC, and loop over the characters to find the
occurrence of specific characters. The task execution time on different
memory requirements is reported in Fig. 1. We can see sudden performance
degradation when the memory requirement exceeds 93MB. Before and after
that point, the task execution time almost linearly increases with the
memory requirement as normal. This is because, when an applicationâ€™s
memory footprint saturates the EPC, excessive secure EPC page swapping
between the EPC and unprotected memory will be incurred \[21\].
Meanwhile, although EPC is 128MB, around 35MB must be allocated to
metadata \[20\]. Note that EPC page swapping is expensive, costing up to
hundreds of thousands of cycles for each swapping, as it does not only
entail data transfer to and from EPC, but also involves page encryption
and integrity check for security guaranteeing \[15\].

Considering the large memory footprint of DNN models, the capacitated
EPC becomes a catastrophe to deep learning based applications requiring
DNN inference in SGX empowered edge cloud. Hence, how to partition a DNN
model and assign the partitions to edge servers to efficiently utilize
the edge resources for fast and secure inference emerges as a new
chal-lenge. Too fine-grained partitioning can avoid EPC page swap-ping,
but may lead to massive inter-partition communication traffic. On the
contrary, coarse-grained partitioning reduces the inter-partition
communication overhead, yet results in high EPC page swapping overhead
and performance degradation. Therefore, instead of simply treating EPC
size as a hard limit, appropriate partitioning and assignment decisions
should be made to balance the partition execution time and
inter-partition communication time for overall inference acceleration.
In this paper, we are motivated to study how to partition and assign a
DNN model to an SGX empowered edge cloud to accelerate distributed DNN
inference. The main contributions of this paper are:

> â€¢ We study how to partition a DNN model and appropri-ately assign the
> partitions to distributed edge servers with SGX, aiming to minimize
> the inference time. The prob-lem is formally stated and proved to be
> NP-hard. To our best knowledge, we are the first to investigate
> distributed inference with the consideration of SGX characteristics.
>
> â€¢ We propose a <u>MEm</u>ory-aware <u>D</u>istributed <u>In</u>ference
> <u>A</u>cceleration (MEDIA) algorithm that well balances the partition
> execution time in SGX and inter-partition com-munication time. The
> achievable guaranteed approxima-tion ratio of MEDIA algorithm is also
> formally analyzed.
>
> â€¢ We implement a prototype system based on DarkNet framework to
> evaluate the proposed MEDIA algorithm, and conduct extensive
> experiments on representative lin-ear and nonlinear DNN models. The
> results show that our
>
> algorithm can reduce the inference time by 19.5%-38.1% in comparison
> with state-of-the-art approaches.

The rest of this paper is organized as follows. Section II introduces
some related work. In Section III, we introduce the system model and
problem statement. Section IV presents MEDIA algorithm and corresponding
theoretical analysis. Section V presents our prototype based evaluation
results. Finally, we conclude this work in Section VI.

> II\. RELATED WORKS

Distributed DNN inference is a potential way to take full ad-vantage of
edge cloud for intelligent applications. Many exist-ing distributed DNN
inference solutions in the literature have targeted inference
acceleration. For example, DNN surgery \[8\] and CRA \[22\] split a DNN
model into two partitions, one processed at the edge and another to the
cloud. The former takes a graph-theoretic approach to find the minimum
cut, and the latter designs a Markov based algorithm to obtain a
near-optimal solution. Mohammed et al. \[23\] propose DINA, which
includes a fine-grained DNN partition policy and matching game based
computation offloading method allowing multiple DNN partitions to be
processed locally by end devices or of-floaded to multiple powerful
nodes for inference acceleration. These solutions mainly target at
general processors without awareness of SGX characteristics, especially
the EPC size limitation. Some also consider memory capacity and
constrain a partition within it. Note that, although EPC size is
limited, the memory footprint could still exceed it, at the cost of
certain performance degradation.

Meanwhile, distributed DNN inference offers the oppor-tunity to utilize
distributed resources, but it also raises the security and privacy
problem, especially in resource sharing infrastructure like edge cloud.
Pioneering researchers have applied various means to guarantee DNN
inference security, such as fully or semi-homomorphic encryption \[12\],
\[24\], \[25\] and multi-party computation \[13\], \[26\], \[27\].
However, these cryptography based methods suffer from severe performance
degradation and limited application scope because of the com-plex
cryptographic operations involved. To facilitate secure DNN inference
with low overhead, SGX is widely advocated and many recent studies have
tried to address the EPC size limitation problem. SECURETF \[28\] uses
model reduction technique to reduce the size of DNN models and improves
inference performance in SGX. Vessels \[20\] overcomes the EPC
limitation through optimizing memory reclaiming during the DNN inference
process. Occlumency \[14\] divides a DNN model into several partitions
and executes them sequentially on a server to cope with the limitation.
However, existing studies usually treat EPC size as a hard limit and
mainly concentrate on a single server to avoid excessive page swapping.
In distributed DNN inference, we argue that certain page swap-ping is
allowable provided that the performance degradation could be compensated
by the reduction of inter-partition com-munication overhead.
Unfortunately, SGX aware distributed DNN inference optimization is still
under-investigated, and this motivates our work.

> 636
>
> Authorized licensed use limited to: Universiteit van Amsterdam.
> Downloaded on May 19,2026 at 12:06:17 UTC from IEEE Xplore.
> Restrictions apply.
>
> Partition 1 Partition 2 Partition 2
>
> <img src="./exohcyla.png"
> style="width:1.16138in;height:0.45113in" /><img src="./finuuexp.png"
> style="width:0.12352in;height:0.11825in" /><img src="./hluboz3x.png"
> style="width:1.01128in;height:0.19097in" /><img src="./0us1me43.png"
> style="width:0.12352in;height:0.11825in" /><img src="./vjgur54m.png"
> style="width:0.12351in;height:0.11825in" /><img src="./ybjc3ss3.png"
> style="width:0.12351in;height:0.11825in" /><img src="./qmhzhbyy.png"
> style="width:1.17769in;height:0.53337in" /><img src="./hptweyip.png"
> style="width:1.08816in;height:0.4067in" /><img src="./3zdqvu1s.png"
> style="width:0.10597in;height:0.10145in" /><img src="./y0y3bgxz.png"
> style="width:0.89497in;height:0.14757in" /><img src="./4tyaad51.png"
> style="width:0.10596in;height:0.10145in" /><img src="./ciood2q4.png"
> style="width:0.10597in;height:0.10145in" /><img src="./4zf4he0r.png"
> style="width:0.73992in;height:0.31185in" /><img src="./oamhcvrf.png"
> style="width:0.10597in;height:0.10145in" />Partition 1 Partition 3
>
> Partition 4 Partition 3 Partition 4 Partition 5
>
> Partition 4 Partition 6 Partition 7
>
> \(a\) Strategy A (b) Strategy B
>
> Fig. 2. AlexNet model partitioning and assignment strategies
>
> TABLE I
>
> INFERENCE TIME BY DIFFERENT STRATEGIES
>
> Inference time
>
> With SGX Without SGX Strategy A 16.1s 5.2s Strategy B 9.1s 6.4s Single
> server 20.4s 11.1s
>
> III\. SYSTEM MODEL AND PROBLEM STATEMENT

A. Motivations

The limited EPC size deeply affects the performance of DNN inference on
SGX empowered edge servers. To take a close look into such impact, we
use widely used AlexNet with 22 layers as an example and evaluate the
inference time in an edge cloud consisting of 4 servers equipped with
Intel Celeron G4930. Two cases, i.e., with and without SGX, are
considered. In either case, two different DNN partitioning and
assignment strategies, as shown in Fig. 2, are applied and the results
on inference time are reported in Table I.

First of all, we can see that applying SGX to guarantee security indeed
is at the cost of long inference time. In any case, the one with SGX
always takes more inference time than the one without SGX. Fortunately,
we can see that the performance loss could be effectively compensated by
exploiting more servers. As shown in Table I, even when SGX is enforced
for security guaranteeing, Strategy B still achieves better performance
than the single server case without SGX.

We can also clearly see that different partitioning and assignment
strategies lead to different inference time. Whatâ€™s especially
interesting is that Strategy B speeds up the infer-ence by 1.77Ã— over
Strategy A when SGX is enforced, but instead, it even performs worse
than Strategy A in the case without SGX. Obviously, the main difference
between the two strategies is on the partition. In the case with SGX,
Strategy A has relatively large partitions (e.g., Partition 2 and
Partition 3 both with 10 layers), whose memory footprint exceeds the EPC
size, resulting in excessive EPC page swapping and long inference time.
On the contrary, in the case without SGX, too fine-grained partitioning
may incur high inter-partition communication overhead, and hence long
inference time.

This example indicates that, to pursue fast secure inference in SGX
empowered edge cloud, we should well balance the page swapping overhead
and communication overhead by taking both EPC size and DNN model
structure into consideration.

B. Problem Statement and Analysis

Next, we formally state the partitioning and assignment problem toward
minimal inference time.

1\) SGX Empowered Edge Cloud: In this paper, we consider an edge cloud
comprising a set N = {1,2,3,...,N} of SGX empowered servers, whose EPC
is in size of E. Any two servers can communicate with each other, either
directly or indirectly. Without loss of generality, Bm,n denotes the
reciprocal communication bandwidth between server m and n. Recall Fig.
1, a sudden performance degradation happens when the memory requirement
exceeds EPC size. Before and after the point, the task execution time
almost linearly increases with the memory usage. Hence, the computing
power of server n can be expressed as a function of memory usage

as

> (
>
> Fn(Î±n) = fn, Î±n â‰¤ E, (1)
>
> n n

where Î±n denotes the memory usage on server n.

2\) DNN Model Partitioning: As we have known, a DNN model can be
represented as a DAG G = (V,E), where V is the set of vertexes
representing the DNN layers and E is the set of edges about the
dependency between layers. A layer v âˆˆ V is indivisible and must be
processed on one server. An edge (u,v) âˆˆ E indicates that u should be
processed before v, and u feeds its output to v. The data size
transferred from layer u to v is indicated as d(u,v), which is
determined by the DNN model structure. Given the structure of a DNN
model, the workload and memory requirement of a layer v âˆˆ V can be
estimated as w(v) and m(v), respectively.

In distributed DNN inference, we partition a large model into a set P of
partitions, each of which consists of a subset of layers (i.e., P âŠ† V,âˆ€P
âˆˆ P) to be executed on one server. The partitions must cover all the
layers in the model. That is,

> âˆªPâˆˆPP = V. (2)

Besides, a layer l âˆˆ V must be included in one and only one partition.
Hence, we have

> P âˆ©Pâ€² = âˆ…,âˆ€P,Pâ€² âˆˆ P,P = Pâ€². (3)

The workload of a partition P can be calculated as w(P) = w(p).
Similarly, the memory footprint of partition P

can be calculated as m(P) = m(p),âˆ€P âˆˆ P. The new edge set L represents
the dependency between different partitions. We use d(Pâ€²,P) to denote
the data size transferred from partitions Pâ€² to P. L and d(Pâ€²,P) can
inherit from E and d(u,v), respectively.

3\) Partition Assignment: The partitions P should be as-signed to edge
servers, which collaboratively process the assigned partitions to
complete the whole inference task. We define binary variables xP,n âˆˆ
{0,1} to indicate whether partition P is assigned to server n (i.e. xP,n
= 1) or not (i.e. xP,n = 0). Each partition P âˆˆ P must be executed on

one server. That is,X

> xP,n = 1,âˆ€P âˆˆ P. (4)
>
> âˆ€nâˆˆN
>
> 637
>
> Authorized licensed use limited to: Universiteit van Amsterdam.
> Downloaded on May 19,2026 at 12:06:17 UTC from IEEE Xplore.
> Restrictions apply.

With respect to the dependency relationship, a partition is ready to
start only when all its predecessors have finished and all the required
input data have been received. Let RT(P) and FT(Q) be the ready time and
finish time of partitions P âˆˆ P and Q âˆˆ P, respectively. Accordingly, we
have

> RT(P) â‰¥ FT(Q)+ xQ,mxP,nd(Q,P), (5) âˆ€P âˆˆ P,Q âˆˆ Pred(P),m âˆˆ N,n âˆˆ N,

where Pred(P) is the predecessor set of partition P.

At most one partition can be executed on an SGX empow-ered server at a
time. If there are multiple partitions assigned to one server, they will
be executed sequentially, i.e.,

> FT(P) â‰¤ ST(Q)\|\|FT(Q) â‰¤ ST(P),âˆ€Q,P âˆˆ P, (6)

where ST(Â·) represents the start time of a partition. This explains why
we distinguish start time from ready time, which actually should satisfy
the following relationship

> Algorithm 1: Edge Selection for MEDIA Partitioning
>
> Input: Model graph G = (V,E); The level of vertexes in V; The weight
> of edges in E.
>
> Output: The subset of edges M. 1 Set M â† âˆ…, P â† âˆ…
>
> 2 for u âˆˆ V following the increasing order of level do
>
> 3 for v âˆˆ Succ(u) following the priority on edges do 4 if (\|Pre(v)\|
> = 1) and (\|Succ(u)\| = 1) then
>
> continue
>
> 5 M â† Mâˆª{(u,v)} 6 for w âˆˆ succ(u) do
>
> 7 if L(u) = L(w)âˆ’1 and there is an (wâ€²,w) âˆˆ M then
>
> 8 M â† M\\(u,v)} 9 end
>
> 10 end 11 end

12 end

> ST(P) â‰¥ RT(P),âˆ€P âˆˆ P. (7)

Once a partition P is started, its finish time can be estimated by its
workload and the assigned serverâ€™s computing power as

> X
>
> FT(P) = ST(P)+ nâˆˆN F(m(P)),âˆ€P âˆˆ P. (8)

By summing up the above, the distributed DNN inference problem to
minimize inference time in SGX empowered edge cloud can be formulated as

> min{max{FT(P)}} PâˆˆP
>
> s.t. : (2)âˆ’(7).

Obviously, this is a nonlinear integer programming problem, which is
non-trivial to solve. Let us consider a special case when EPC is
sufficient and all partitions have been determined. The thing we need to
do is to assign the partitions to appro-priate edge servers to minimize
inference time. Essentially, it is equivalent to assigning tasks of a
DAG to heterogeneous processors to minimize the makespan. This problem
has been formulated into a flow-shop scheduling problem and proved to be
NP-hard \[29\]. Therefore, the DNN model partitioning and assignment
problem, as a general case, is NP-hard.

> IV\. MEMORY-AWARE DISTRIBUTED DNN INFERENCE ACCELERATION ALGORITHMS

To tackle the computation complexity, we design <u>ME</u>mory-aware
<u>D</u>istributed <u>I</u>nference <u>A</u>cceleration (MEDIA)
algorithm in this section, which mainly consists of partitioning phase
and assignment phase.

A. MEDIA Partitioning

In the partitioning phase, we divide a DNN model into a group of
partitions and restructure the partitions into a coarse DAG, with the
consideration of EPC characteristics (i.e., EPC capacity and performance
degradation after exceeding the ca-pacity). Based on multilevel graph
partitioning methods \[30\],

we design our MEDIA partitioning strategy, which consists of the
following two stages.

> â€¢ First, we find a set of edges where the vertexes along each edge can
> be collapsed.
>
> â€¢ Next, we generate partitions via collapsing the vertexes along these
> edges with the consideration of EPC charac-teristics.

The details of these two stages are presented in Algorithm 1

and Algorithm 2, respectively.

1\) Edge Selection: As we assign the coarse graph to edge servers in the
unit of partition, the partition assign-ment decisions are related to
the estimated ready time and finish time of partitions. According to
(5), it is impossi-ble to estimate the time if the graph is cyclic.
Therefore, we should first find a subset of edges in G, i.e., M =
{(u1,v1),(u2,v2),...,(uk,vk)} âŠ† E to ensure that the coarse graph GM to
be created is acyclic.

Lemma 1 The coarse graph GM is acyclic, if M =
{(u1,v1),(u2,v2),...,(uk,vk)} satisfies the following con-straints
\[31\].

> â€¢ Constraint 1: âˆ€i âˆˆ {1,2,...,k}, Succ(ui) = {vi}, or Pred(vi) = {ui},
>
> â€¢ Constraint 2: âˆ€i = j âˆˆ {1,2,...,k}, (ui,vj) âˆˆ/ E, or L(ui)+1 =
> L(vj),

where Succ(ui) represents the immediate successors of ui and L(v) is the
topological order of vertex v in G.

The topological order could be obtained via any graph traverse algorithm
such as depth-first search (DFS).

Following Lemma 1, we propose our edge selection algo-rithm in Algorithm
1 to produce edge set M, based on which an acyclic graph GM can be
constructed. We traverse the vertexes of graph G via DFS as shown in
line 2. For each vertex u, if its successor v does not satisfy
Constraint 1 in Lemma 1, vertexes u and v cannot be collapsed. Then, we

> 638
>
> Authorized licensed use limited to: Universiteit van Amsterdam.
> Downloaded on May 19,2026 at 12:06:17 UTC from IEEE Xplore.
> Restrictions apply.
>
> Algorithm 2: Memory-aware MEDIA Partitioning
>
> Input: The subset of edges M Output: DNN partitioning results P.
>
> 1 for (u,v) âˆˆ M do
>
> 2 if Both vertexes in (u,v) are not collapsed then 3 if Check({u},
> {v}) then
>
> 4 Generate a new partition P = {u,v} 5 P â† PâˆªP
>
> 6 end
>
> 7 else if Both vertexes in (u,v) are collapsed then 8 Find the
> partition P âˆˆ P includes u
>
> 9 Find the partition Pâ€² âˆˆ P includes v 10 if Check(P, Pâ€²) then
>
> 11 P â† P âˆªPâ€² 12 end
>
> 13 else if Only one vertex in (u,v) is not collapsed then
>
> 14 Find partition P âˆˆ P with the collapsed vertex 15 Let w denote the
> uncollapsed vertex in (u,v) 16 if Check(P, {w}) then
>
> 17 P â† P âˆª{w} 18 end

19 end 20 end

21 Function Check(P, Pâ€²):

> 22 if T(P âˆªPâ€²) â‰¤ T(P)+ T(P,Pâ€²)+ T(Pâ€²) or m(P âˆªPâ€²) â‰¤ E then return true

23 return false 24 end

> move to its successor v, as shown in line 4. If v satisfies Constraint
> 1, edge (u,v) will be added into subset M in line 5. We further check
> if vertex u satisfies Constraint 2 or not. For any other successor of
> u, say w, if there is an edge (wâ€²,w) âˆˆ M and L(u) = L(w)âˆ’1, adding
> edge (u,v) into M will contradict Constraint 2, In this case, edge
> (u,v) should be removed from M, as shown in line 6 to line 10. We
> repeat this process until all edges (u,v) satisfying both Constraint 1
> and Constraint 2 are added into M.
>
> 2\) Graph Partition: Next, we will construct an acyclic coarse graph
> GM based on the selected edge set M via collapsing the vertexes into
> partitions. The major concern here is on the EPC. Basically, we
> greedily collapse dependent vertexes into the same partition, subject
> to the EPC capacity, to avoid inter-partition communication. However,
> the newly formed partitionâ€™s memory requirement may be beyond the EPC
> size. Note that MEDIA does not treat the EPC size as a hard limit and
> allows overranging, provided that the incurred performance degradation
> is tolerable. That is, MEDIA collapses two partitions into one if the
> achieved inference time is less than executing them separately,
> despite the overranging.
>
> We estimate the execution time of a partition as
>
> T(P) = PnâˆˆN Fw(m(P))/\|N\|. (9)

During the inference process, certain data must be transferred between
dependent partitions. The inter-partition communica-tion time between
two dependent partitions, say P and Pâ€², can be estimated as

> T(P,Pâ€²) = P d(P,Pâ€²) . (10) mâˆˆN nâˆˆN m,n

Now, we can define function Check(P, Pâ€™) to assess whether two
partitions P and Pâ€² should be collapsed into one or not, as shown in
lines 21-24 in Algorithm 2. If the total memory requirement is within
the EPC size, i.e., m(P âˆª Pâ€²) â‰¤ E, without doubt that we should
construct a large partition by collapsing them. Otherwise, if T(P âˆªPâ€²) â‰¤
T(P)+ T(P,Pâ€²)+ T(Pâ€²), we still put them into one.

Then, we can apply the function Check() and traverse the edges in M to
construct partitions. We will meet the following three situations.

> â€¢ If both vertexes of edge (u,v) are not collapsed, we apply Check()
> to decide whether they can be collapsed into one partition or not. If
> true, we will generate a new partition containing u and v (lines 2-6).
>
> â€¢ If both vertexes of edge (u,v) have been collapsed, we find the
> partition P with u and the partition Pâ€² with v. We will collapse P and
> Pâ€² into one large partition if function Check() tells us it is
> beneficial to do so. (lines 7-12).
>
> â€¢ If only one vertex of edge (u,v) has been collapsed, we first find
> the partition P including the collapsed vertex, and apply function
> Check() to check whether another vertex can be collapsed into P or not
> (lines 13-19).

After traversing all the edges in M, we can get the partitions of a DNN
model and obtain the corresponding coarse DAG GM = {P,L}.

B. MEDIA Assignment

After obtaining GM, we next should assign the partitions P into
appropriate edge servers toward the minimum inference time. During
partition assignment, first of all, the topological order of GM must be
guaranteed. That is, the predecessors of a partition (say P) should be
assigned before P. For example, the partition with the input layer must
be assigned at the very beginning. Secondly, the partition with high
resource requirements should be assigned as early as possible so as to
find a server with sufficient resources. With respect to the above two
issues, we define the assignment priority of a partition P as

Priority(P) = max {T(P)+T(P,Pâ€²)+Priority(Pâ€²)}. Pâ€²âˆˆsucc(P)

> \(11\)

Lemma 2 The decreasing order of priority provides a topo-logical
ordering of partitions in the graph.

Proof: From the definition in (11), for any edge (P,Pâ€²) âˆˆ L in the graph
GM, we always have Priority(P) â‰¥ Priority(Pâ€²). The topological order can
be guaranteed by the decreasing order of priority.

> 639
>
> Authorized licensed use limited to: Universiteit van Amsterdam.
> Downloaded on May 19,2026 at 12:06:17 UTC from IEEE Xplore.
> Restrictions apply.
>
> Algorithm 3: MEDIA Assignment Algorithm
>
> 1 for P âˆˆ P do
>
> 2 Calculate the priority of partition P following (11) 3 end
>
> 4 for P âˆˆ P following decreasing order of priorities do 5 T â† âˆ…
>
> 6 for n âˆˆ N do
>
> 7 Calculate FT(P) on server n via (5)-(7) 8 T â† Tâˆª{FT(P)}
>
> 9 end
>
> 10 Find the minimum FT(P) from set T and assign the partition P to the
> corresponding server s

11 end

> By Lemma 2, we can conclude that the partitions with higher priority
> should be assigned earlier to ensure their topological dependency.
> Based on such principle, we propose a prioritized MEDIA Assignment
> algorithm, as shown in Algorithm 3. We first calculate the priority of
> each partition in line 2. Then, we traverse all the partitions
> following the decreasing order of partition priority. We choose the
> unas-signed partition P with the highest priority and calculate its
> expected finish time on each server following (5)-(7), in lines 6 to
> 9. After that, partition P will be assigned to the server that
> achieves the lowest finish time FT(P) in line 10. The above procedure
> repeats until all partitions are assigned.
>
> C. Theoretical Analysis of MEDIA
>
> Next, we analyze the gap between the inference time ob-tained by MEDIA
> and the optimal solution, which are denoted as Omedia and Oopt,
> respectively. For tractability, we discrete the inference time Omedia
> into a number of time slots. These time slots can be categorized into
> two subsets A and B, where busy time slots A is defined as the set of
> all time slots when all edge servers are busy, and idle time slots B
> includes all time slots when at least one edge server is idle.
>
> We first consider the idle time slots B represented by a disjoint
> union of q open time intervals (blt,brt), i.e., B =
> (bl1,br1)âˆª(bl2,br2)âˆª...âˆª(blq ,brq ), where bl1 \< br1 \< bl2 \< br2 \<
> ... \< blq \< brq .
>
> Lemma 3 We can always extract a chain of partitions as C : Pl â†’ Plâˆ’1 â†’
> ... â†’ P1 from the coarse graph that satisfies
>
> q l lâˆ’1
>
> (br âˆ’bl ) â‰¤ ( max Tmin(Pk))+ Ttrans, (12) j=1 k=1 min k=1
>
> where Ttrans is the maximum data transmission time in chain C,
> Tmin(Pk) is the minimum execution time of partition Pk in the edge
> cloud, and Fmax and Fmin denote the maximum and minimum computing
> power of edge servers.
>
> Proof: Let P1 denote the last partition assigned by MEDIA algorithm.
> There are three cases regarding the start time of P1, i.e.,
>
> â€¢ ST(P1) â‰¤ bl1.
>
> â€¢ ST(P1) âˆˆ B. That is, there exists an integer h, h â‰¤ q, such that blh
> â‰¤ ST(P1) â‰¤ brh.
>
> â€¢ ST(P1) âˆˆ A but ST(P1) \> bl1. That is, there exists an integer h,h â‰¤
> q âˆ’1, such that brh â‰¤ ST(P1) â‰¤ blh+1 or brq â‰¤ ST(P1).

For the above three cases, we can always add one or more partitions to
the left of the chain to satisfy (12). In detail, we construct C for
each case as follows.

Case 1: In this case, the partition P1 by itself constitutes a chain
that satisfies (12).

Case 2: If ST(P1) falls into B, we can find another partition P2 to
construct chain C following two sub-cases independently as below.

SUB-CASE 1: If P1 does not become ready until ST(P1), indicating that
ST(P1) = RT(P1), we simply add the last finished predecessor of P1 as P2
into the chain.

SUB-CASE 2: If P1â€™s ready time is earlier than ST(P1), i.e., RT(P1) \<
ST(P1), by the definition of B, there must be an idle server n âˆˆ N
during (blh,brh) where RT(P1) \< brh, indicating that P1 is ready when n
is idle. Intuitively, P1 can start earlier on n but actually MEDIA does
not assign P1 to server n to make it start earlier. According to MEDIA,
there must exist another assignment satisfying FT(P1) â‰¤ FTn(P1) where
FTn(P1) be the finish time of P1 assigned to server n. Let P2 denote the
last finished predecessor of P1. It is obvious that

> FTn(P1) â‰¤ FT(P2)+ Ttrans +Tmax(P1), (13)

where Tmax(P1) = Fmax Tmin(P1) denotes the maximum execution time of
partition P1 in the edge cloud. Then, we can construct the chain via
inserting partition P2 into the left of P1 and derive that

> Ttrans + Fmax Tmin(P1) â‰¥ FT(P1)âˆ’FT(P2). (14) min

Case 3: Same as Case 2, we insert the last finished imme-diate
predecessor of P1 into the chain, and we can still obtain (14).

When a new partition is inserted into the chain, it will meet one of the
three cases mentioned above. If Case 1 happens, we are done. Otherwise,
we need to add more partitions in the way mentioned in Case 2 or Case 3.
Such process repeats until Case 1 happens. Finally, chain C satisfying
(12) is successfully constructed.

> Hence, we can derive the idle time of MEDIA as follows.

Lemma 4 In MEDIA algorithm, the total idle time of all the servers
satisfies

> lâˆ’1
>
> Tidle(n) â‰¤ \|N\|( max Oopt + Ttrans), (15) nâˆˆN min k=1

where Tidle(n) denotes the idle time of server n.

Proof: It is obvious that the total idle time on one server is smaller
than the total time in set B. Therefore, we have

> X X
>
> Tidle(n) â‰¤ \|N\| (brj âˆ’blj ). (16)
>
> nâˆˆN j=1
>
> 640
>
> Authorized licensed use limited to: Universiteit van Amsterdam.
> Downloaded on May 19,2026 at 12:06:17 UTC from IEEE Xplore.
> Restrictions apply.

With Lemma 3 and (16), we can derive

> l lâˆ’1
>
> Tidle(n) â‰¤ \|N\|( ( max Tmin(Pk))+ Ttrans). nâˆˆN k=1 min k=1
>
> \(17\)

In addition, many existing studies \[32\], \[33\] have already proved
that, for any DAG, its optimal makespan is longer than the makespan of
any chain extracted from it. Hence, we can further conclude that

> X
>
> Tmin(Pk) â‰¤ Oopt. (18)
>
> k=1
>
> TABLE II

CPU MODELS OF SGX-ENABLED SERVERS FOR EXPERIMENTS

> Server ID CPU Type Frequency Server 1 Intel Core i5-11600 4.60GHz
> Server 2 Intel Core i3-10100 3.60GHz Server 3 Intel Core i5-6500
> 3.20GHz Server 4 Intel Celeron G4930 3.20GHz

||
||
||
||
||

> **VGG16** **NiN**

Now, we can derive (15) with (17) and (18). Then, we consider the busy
time of MEDIA.

Lemma 5 In MEDIA algorithm, the total busy time satisfies XTbusy(n) â‰¤
\|N\|Fmax Oopt, (19) nâˆˆN min

> 1 2 4 6 8 10 12 14 16 18 20 22 23 3 5 7 9 11 13 15 17 19 21
>
> **AlexNet**

||
||
||
||
||
||
||

> **ResNet18**
>
> 9

10 **Inception** **Module**

where Tbusy(n) denotes the busy time of server n.

Proof: A server n âˆˆ N is considered as busy whenever there is a
partition being executed. Hence, the left-hand of (19) is equal to the
total time of executing all assigned partitions.

That is, X X

> Tbusy(n) = Texe(n), (20)
>
> nâˆˆN nâˆˆN

where Texe(n) denotes the time of executing partitions on server n.
Obviously, nâˆˆN Texe(n) cannot exceed

> Fmax PâˆˆP Tmin(P). Hence, we have
>
> XTbusy(n) â‰¤ Fmax X Tmin(P). (21) nâˆˆN min PâˆˆP

Existing work \[34\] has proved that Tmin(P) â‰¤ \|D\|Oopt. Thus, (19) can
be derived from (21).

With Lemma 4 and Lemma 5, we can obtain the upper bound of Omedia as
follows.

Theorem 1 The inference time of MEDIA always satisfies

> lâˆ’1
>
> Omedia â‰¤ 2 max Oopt + Ttrans. min k=1
>
> Proof: As Omedia consists of the busy and idle time, it

can be expressed as X

> Omedia = (Tidle(n)+ Tbusy(n))/\|N\|. (22)
>
> nâˆˆN

According to Lemma 4 and Lemma 5, (22) can be rewritten

as X

> Omedia = (Tidle(n)+ Tbusy(n))/\|N\|
>
> nâˆˆN
>
> lâˆ’1
>
> â‰¤ 2 max Oopt + Ttrans. min k=1

Therefore, our MEDIA algorithm can achieve inference time no worse than
2Fmax Oopt + lâˆ’1 Ttrans.

> Fig. 3. The structure of linear and nonlinear DNN models
>
> V. PERFORMANCE EVALUATION

To evaluate the performance of MEDIA, we have imple-mented a prototype
system based on DarkNet. In this section, we report our prototype
implementation, experiment settings, and performance evaluation results.

A. Implementation and Experimental Setup

1\) Prototype system implementation: The DarkNet cannot be ported in SGX
directly because system calls and CUDA are forbidden in SGX. To build
the prototype system, we re-implement all system calls and the modules
relying on CUDA, such as information logging, fully-connected layer
module and convolution layer module. By such means, we successfully port
the DarkNet framework into SGX and realize the prototype system.

2\) Prototype system setup: As shown in Table II, the experiment
environment consists of 4 servers equipped with SGX 2.7 environment and
Ubuntu 18.04 operating system to emulate an SGX empowered edge cloud.
These servers are connected to each other and the average bandwidth
between any two servers is set as 10Mbps via wonder shaper in default.

3\) DNN models: To evaluate the adaptability of MEDIA, we adopt 6 DNN
models in different structures, including 2 linear models as NiN and
VGG16, and 4 nonlinear models as ResNet18, AlexNet, InceptionV3 and
InceptionV4. Their structures are shown in Fig. 3.

4\) Comparison algorithms: We compare MEDIA against state-of-the-art
schemes, including Occlumency (OCC) \[14\], Dynamic Adaptive DNN surgery
(DADS) \[8\] and Distributed INference Acceleration (DINA) \[23\]. We
run each experiment 10 times and report the average inference time with
an error bar representing standard deviation.

> 641
>
> Authorized licensed use limited to: Universiteit van Amsterdam.
> Downloaded on May 19,2026 at 12:06:17 UTC from IEEE Xplore.
> Restrictions apply.

<img src="./gfxufokq.png"
style="width:0.78571in;height:0.54398in" /><img src="./elejagxl.png"
style="width:0.76886in;height:0.54398in" /><img src="./iqthnijh.png"
style="width:2.02729in;height:0.35203in" />

> <img src="./bqbs4oq0.png"
> style="width:0.73537in;height:0.54398in" />
>
> <img src="./utnvhmdj.png"
> style="width:0.8192in;height:0.54398in" /><img src="./kffoytej.png"
> style="width:0.8192in;height:0.54398in" /><img src="./0fte2uih.png"
> style="width:0.73537in;height:0.54398in" /><img src="./yzaj4q4c.png"
> style="width:0.29013in;height:0.39998in" /><img src="./db2ffrbl.png"
> style="width:0.30002in;height:0.38085in" /><img src="./gaqpnylx.png"
> style="width:0.29344in;height:0.38701in" /><img src="./zkzfoc1i.png"
> style="width:0.29675in;height:0.31054in" /><img src="./d4g3odyo.png"
> style="width:0.29404in;height:0.39255in" /><img src="./4z0yox3b.png"
> style="width:0.29713in;height:0.31011in" />(a) NiN (b) VGG16 (c)
> ResNet18 (a) NiN (b) VGG16 (c) ResNet18
>
> \(d\) AlexNet (e) InceptionV3 (f) InceptionV4 (d) AlexNet (e)
> InceptionV3 (f) InceptionV4

Fig. 4. The inference time of different DNN models by different
algorithms

> Partition 1 Partition 3 Partition 1 Partition 2
>
> Partition 2 Partition 4 Partition 4 Partition 3
>
> Fig. 5. The partition result of ResNet18 obtained by MEDIA

B. The Inference Time of Different DNN Models

We first evaluate the inference time and memory usage of MEDIA on all 6
DNN benchmarks mentioned above. The results are shown in Fig. 4 and Fig.
6, respectively.

It can be observed that MEDIA achieves the lowest infer-ence time among
all schemes, as shown in Fig. 4. The high efficiency of our MEDIA is
validated by the fact that it signifi-cantly reduces the inference time
by 19.5%, 38.1% and 29.4% in comparison with OCC, DNIA and DADS,
respectively. We attribute this inference time speedup to better
partitioning and assignment decisions made by MEDIA. Instead of simply
treating EPC size as a hard limit, MEDIA allows a partitionâ€™s memory
footprint to exceed EPC size, and balances the EPC page swapping
overhead and the inter-partition communication overhead for overall
inference acceleration. It is noticeable that the inference time of NiN
by all four algorithms is close. This is mainly because the total memory
requirement of NiN model is about 78.4MB, smaller than EPC size. As a
result, EPC page swapping will not happen during the execution of NiN
and there is not much optimization space for partitioning and
assignment.

Another interesting finding is that OCC algorithm some-times achieves
comparable inference time to MEDIA in Figs. 4(a)âˆ¼4(c). Note that the
advantage of MEDIA over OCC is that MEDIA can well leverage distributed
edge servers and enable parallel DNN partition execution. However, when
the structure of DNN model is linear, all partitions must be executed
one by one sequentially. In our experiments, the coarse DAGs of linear
DNN models NiN and VGG16 are still linear. Although ResNet18 itself is
nonlinear, it is partitioned and restructured into a coarse DAG in
linear structure, as shown in Fig. 5. By OCC or MEDIA, all partitions of

> Fig. 6. The peak memory usage of different algorithms on different
> servers

these three models will be assigned to the server with the highest
computing power and executed sequentially. Hence, the inference time of
OCC and MEDIA is comparable. While, for most non-linear models (e.g.,
AlexNet, InceptionV3 and InceptionV4 in Figs. 4(d)-4(f)), their
restructured coarse DAGs are still non-linear. The partitions in
non-linear coarse DAG can be assigned to different servers and executed
in parallel. In this case, compared with OCC, MEDIA significantly
reduces the inference time by 28.3%, 47.6% and 39.8% for AlexNet,
InceptionV3 and InceptionV4, respectively.

To further validate the fact that our MEDIA and OCC effec-tively take
EPC size into consideration, we present the peak memory usages of all
four algorithms in Fig. 6. It can be seen that both MEDIA and OCC ensure
the peak memory usage of each partition around 93MB for most DNN models.
However, in InceptionV3 and InceptionV4 cases, the peak memory usage of
MEDIA, as almost up to 120MB, exceeds the EPC size. Remember that MEDIA
does not treat EPC size as a hard limit, instead it allows EPC
overranging to trade execution performance degradation with
inter-partition communication minimization for overall performance
optimization. One may also notice that the peak memory usage of VGG16 is
as large as 836.4MB. This is because that some indivisible layers of
VGG16 are large. For example, layer 20 in VGG16 (see Fig. 3) itself
requires more than 800MB memory. In such circumstances, the secure EPC
page swapping is inevitable. The optimization space left for MEDIA
becomes limited. Nevertheless, MEDIA still shows more advantages than
other algorithms in most DNN models.

C. The Impact of Server Number

Next, we present the DNN inference time with different number of
servers. In this experiment, we add SGX-enabled servers with different
computing power into the edge cloud by the following order: 2 servers
with Intel Celeron G4930, 4 servers with Intel Core i5-5600, 1 server
with Intel Core i3-10100 and 1 server with Intel Core i5-11600 to test
the algorithmsâ€™ sensitivity on heterogeneous computing power.

As shown in Fig. 7, the inference time shows as a non-increasing trend
with the increase of server number in all cases,

> 642
>
> Authorized licensed use limited to: Universiteit van Amsterdam.
> Downloaded on May 19,2026 at 12:06:17 UTC from IEEE Xplore.
> Restrictions apply.
>
> <img src="./33gb1bpy.png"
> style="width:0.69415in;height:0.43062in" /><img src="./1wb5kvfo.png"
> style="width:0.74041in;height:0.46645in" />

transferring. Hence, the inference time will not be affected by network
bandwidth.

> \(a\) NiN
>
> <img src="./hllbckux.png"
> style="width:0.73991in;height:0.34509in" />
>
> \(d\) AlexNet
>
> \(b\) VGG16

<img src="./x2ir3hmk.png"
style="width:0.74325in;height:0.3662in" />

> \(e\) InceptionV3

<img src="./a2xryfps.png"
style="width:0.76732in;height:0.40013in" />

> \(c\) ResNet18

<img src="./inokqsec.png"
style="width:0.73657in;height:0.37733in" />

> \(f\) InceptionV4

<img src="./5vaq0pmk.png"
style="width:0.69415in;height:0.11743in" />  
\$

\$

\$

> \$
>
> !&% "\$
>
> \(a\) NiN

<img src="./0qbog0mi.png" style="width:0.73657in" /><img src="./f1kdcbko.png"
style="width:0.73822in;height:0.17261in" />\#

> \#
>
> \#
>
> \#

<img src="./xegqqcv1.png"
style="width:0.73488in;height:0.15254in" />\#

\#

\#

\#

\#

> %\$ !#
>
> \(b\) VGG16

<img src="./0vbzbm5s.png"
style="width:0.73657in;height:0.25353in" />\#

> \#
>
> \#
>
> \#
>
> \$

\$

\$

\$

> !&% "\$
>
> \(c\) ResNet18

<img src="./mj4mxb3c.png"
style="width:0.73991in;height:0.28916in" />\#

\#

\#

> \#
>
> Fig. 7. The inference time on different server numbers
>
> %\$ !#

\(d\) AlexNet

\#  
%\$ !#

> \(e\) InceptionV3

\#  
%\$ !#

> \(f\) InceptionV4

and our MEDIA always achieves the best performance. On average, the
inference time of MEDIA is reduced by 11.6%, 27.8% and 17.3% in
comparison with OCC, DNIA and DADS, respectively. This is because MEDIA
always tries to fully utilize distributed computing resources in edge
cloud and the possible parallelism of DNN models to efficiently speed up
the DNN inference. We also observe that the inference time of all
algorithms in Figs. 7(a)âˆ¼7(c) does not change too much when the server
number grows from 3 to 6. As we have known, the NiN, VGG16 and ResNet18
models are all linear. Their partitions are executed on the most
powerful server. While, the 4 newly added servers are in the same type,
and hence the inference time remains almost the same from 3 servers to 6
servers. However, when more powerful servers 7 and 8 are added, they are
selected for execution and the inference time decreases, as shown in
Figs. 7(a)âˆ¼7(c).

In addition, from Figs. 7(d)âˆ¼7(f), we further observe that InceptionV3
and InceptionV4 are more sensitive to the server number and computing
power than AlexNet. For example, the inference time of InceptionV3 and
InceptionV4 by MEDIA is reduced by 68.3% and 58.2%, respectively, when
the server number is increased from 1 to 8 in Fig. 7(e) and Fig. 7(f).
But when it comes to AlexNet, the inference time of MEDIA is only
reduced by 49.3%, as shown in Fig. 7(d). It is because that the
InceptionV3 and InceptionV4 have more independent layers than AlexNet,
as shown in Fig. 3. Hence, the partitions of AlexNet are executed
parallelly on up to 2 servers, while InceptionV3 and InceptionV4 can
well leverage all servers.

D. The Impact of Network Bandwidth

Finally, we investigate the effect of network bandwidth via increasing
the bandwidth from 1Mbps to 10Mbps, and the experiment results are shown
in Fig. 8. Once again, MEDIA still always achieves the best performance,
speeding up the inference by 1.25Ã—, 1.85Ã— and 1.52Ã— over OCC, DNIA and
DADS, respectively. Besides, for NiN, VGG16 and ResNet18, the inference
time does not change too much in Figs. 8(a)âˆ¼8(c). As we have known, all
the partitions of these models are assigned to the most powerful server,
without data

> Fig. 8. The inference time on different average network bandwidths

For AlexNet, InceptionV3 and InceptionV4, we can see that the inference
time of MEDIA, DNIA and DADS de-creases with the increase of network
bandwidth, as shown in Figs. 8(d)âˆ¼8(f). This is because higher bandwidth
implies lower inter-partition communication time, resulting in faster
inference. Furthermore, we discover another phenomenon that, for
InceptionV3 and InceptionV4, the inference time by MEDIA is reduced by
almost 50% when the average network bandwidth is increased from 1Mbps to
10Mbps in Fig. 8(d) and Fig. 8(e), but only 27% for AlexNet in Fig.
8(d). As we have known, compared with AlexNet, MEDIA produces more
partitions in the cases of InceptionV3 and InceptionV4 to exploit the
distributed computing resources. This implies higher inter-partition
data transferring needs and therefore more sensitive to network
bandwidth. Consequently, Incep-tionV3 and InceptionV4 benefit more than
AlexNet from the increase of network bandwidth.

Whatâ€™s more, from Figs. 8(d)âˆ¼8(f), we find that the infer-ence time of
MEDIA is not affected too much by network bandwidth, and even is close
to the inference time of OCC, when the bandwidth is below 3Mbps. When
the bandwidth is too small, MEDIA will assign all partitions to one
powerful server to avoid long inter-partition communication time. In
this case, MEDIA achieves similar performance with OCC. However, as the
network bandwidth increases, MEDIA is able to well balance execution
time and communication time for overall inference acceleration, and
therefore becomes advan-tageous over OCC.

> VI\. CONCLUSION

In this paper, we investigate how to accelerate distributed DNN
inference in SGX empowered edge cloud. Being aware of the capacitated
EPC, we formulate the DNN model par-titioning and partition assignment
problem for minimal in-ference time into a nonlinear integer programming
form, and prove it as NP-hard. We further propose MEDIA algo-rithm that
first reconstructs the DNN model into an acyclic coarse graph to well
balance EPC page swapping overhead

> 643
>
> Authorized licensed use limited to: Universiteit van Amsterdam.
> Downloaded on May 19,2026 at 12:06:17 UTC from IEEE Xplore.
> Restrictions apply.

(i.e., computation performance degradation) and inter-partition
communication overhead, and then assigns the partitions to edge servers
to efficiently utilize distributed resources. The guaranteed
approximation ratio of MEDIA is theoretically analyzed. We practically
implement MEDIA and build a prototype system. Via extensive comparison
with state-of-the-art schemes, the results on commonly-used DNN models
show that MEDIA achieves equivalent performance to OCC \[14\] on linear
models and greatly outperforms all existing schemes on non-linear
models. Averagely, it can significantly reduce the inference time by
19.5%-38.1%.

> REFERENCES
>
> \[1\] X. Zhang, Y. Wang, S. Lu, L. Liu, L. Xu, and W. Shi, â€œOpenEI: An
> Open Framework for Edge Intelligence,â€ in Proceedings of IEEE
> International Conference on Distributed Computing Systems (ICDCS), pp.
> 1840â€“1851, 2019.
>
> \[2\] H. Zhou, W. Li, Z. Kong, J. Guo, Y. Zhang, B. Yu, L. Zhang, and
> C. Liu, â€œDeepbillboard: Systematic Physical-World Testing of
> Au-tonomous Driving Systems,â€ in Proceedings of IEEE/ACM International
> Conference on Software Engineering (ICSE), pp. 347â€“358, 2020.
>
> \[3\] L. Zeng, X. Chen, Z. Zhou, L. Yang, and J. Zhang, â€œCoEdge:
> Co-operative DNN Inference with Adaptive Workload Partitioning Over
> Heterogeneous Edge Devices,â€ IEEE/ACM Transactions on Networking
> (TON), vol. 29, no. 2, pp. 595â€“608, 2020.
>
> \[4\] A. Mahmood, M. Bennamoun, S. An, and F. Sohel, â€œResfeats:
> Residual Network based Features for Image Classification,â€ in
> Proceedings of IEEE International Conference on Image Processing
> (ICIP), pp. 1597â€“ 1601, 2017.
>
> \[5\] Z. Xu, L. Zhao, W. Liang, O. F. Rana, P. Zhou, Q. Xia, W. Xu,
> and G. Wu, â€œEnergy-Aware Inference Offloading for DNN-Driven
> Applications in Mobile Edge Clouds,â€ IEEE Transactions on Parallel and
> Distributed Systems (TPDS), vol. 32, no. 4, pp. 799â€“814, 2020.
>
> \[6\] J. Du, X. Zhu, M. Shen, Y. Du, Y. Lu, N. Xiao, and X. Liao,
> â€œModel Parallelism Optimization for Distributed Inference Via
> Decoupled CNN Structure,â€ IEEE Transactions on Parallel and
> Distributed Systems (TPDS), vol. 32, no. 7, pp. 1665â€“1676, 2020.
>
> \[7\] S. Teerapittayanon, B. McDanel, and H.-T. Kung, â€œDistributed
> Deep Neural Networks over the Cloud, the Edge and End Devices,â€ in
> Pro-ceedings of IEEE International Conference on Distributed Computing
> Systems (ICDCS), pp. 328â€“339, 2017.
>
> \[8\] C. Hu, W. Bao, D. Wang, and F. Liu, â€œDynamic Adaptive DNN
> Surgery for Inference Acceleration on the Edge,â€ in Proceedings of
> IEEE International Conference on Computer Communications (INFOCOM),
> pp. 1423â€“1431, 2019.
>
> \[9\] J. Wei, Y. Zhang, Z. Zhou, Z. Li, and M. A. Al Faruque, â€œLeaky
> DNN: Stealing Deep-learning Model Secret with GPU Context-switching
> Side-channel,â€ in Proceedings of IEEE/IFIP International Conference on
> Dependable Systems and Networks (DSN), pp. 125â€“137, 2020.

\[10\] Y. Liu, L. Wei, B. Luo, and Q. Xu, â€œFault Injection Attack on
Deep Neu-ral Network,â€ in Proceedings of IEEE/ACM International
Conference on Computer-Aided Design (ICCAD), pp. 131â€“138, 2017.

\[11\] M. Jagielski, A. Oprea, B. Biggio, C. Liu, C. Nita-Rotaru, and B.
Li, â€œManipulating Machine Learning: Poisoning Attacks and
Countermea-sures for Regression Learning,â€ in Proceedings of IEEE
Symposium on Security and Privacy (S&P), pp. 19â€“35, 2018.

\[12\] B. Reagen, W.-S. Choi, Y. Ko, V. T. Lee, H.-H. S. Lee, G.-Y. Wei,
and D. Brooks, â€œCheetah: Optimizing and Accelerating Homomorphic
Encryption for Private Inference,â€ in Proceedings of IEEE International
Symposium on High-Performance Computer Architecture (HPCA), pp. 26â€“39,
2021.

\[13\] P. Mishra, R. Lehmkuhl, A. Srinivasan, W. Zheng, and R. A. Popa,
â€œDelphi: A Cryptographic Inference Service for Neural Networks,â€ in
Proceedings of USENIX Security Symposium (USENIX Security), pp.
2505â€“2522, 2020.

\[14\] T. Lee, Z. Lin, S. Pushp, C. Li, Y. Liu, Y. Lee, F. Xu, C. Xu, L.
Zhang, and J. Song, â€œOcclumency: Privacy-preserving Remote Deep-learning
Inference Using SGX,â€ in Proceedings of ACM International Conference on
Mobile Computing and Networking (MobiCom), pp. 1â€“17, 2019.

\[15\] V. Costan and S. Devadas, â€œIntel SGX Explained,â€ IACR Cryptol.
ePrint Arch., vol. 2016, no. 86, pp. 1â€“118, 2016.

\[16\] S. Arnautov, B. Trach, F. Gregor, T. Knauth, A. Martin, C.
Priebe, J. Lind, D. Muthukumaran, D. Oâ€™keeffe, M. L. Stillwell, D.
Goltzsche, D. Eyers, R. Kapitza, P. Pietzuch, and C. Fetzer, â€œSCONE:
Secure Linux Containers with Intel SGX,â€ in Proceedings of USENIX
Symposium on Operating Systems Design and Implementation (OSDI), pp.
689â€“703, 2016.

\[17\] C.-C. Tsai, D. E. Porter, and M. Vij, â€œGraphene-SGX: A Practical
Library OS for Unmodified Applications on SGX,â€ in Proceedings of USENIX
Annual Technical Conference (ATC), pp. 645â€“658, 2017.

\[18\] M. Orenbach, P. Lifshits, M. Minkin, and M. Silberstein, â€œEleos:
ExitLess OS Services for SGX Enclaves,â€ in Proceedings of ACM European
Conference on Computer Systems (EuroSys), pp. 238â€“253, 2017.

\[19\] C. Priebe, K. Vaswani, and M. Costa, â€œEnclavedb: A secure
database using sgx,â€ in Proceedings of IEEE Symposium on Security and
Privacy (S&P), pp. 264â€“278, 2018.

\[20\] K. Kim, C. H. Kim, J. J. Rhee, X. Yu, H. Chen, D. Tian, and B.
Lee, â€œVessels: Efficient and Scalable Deep Learning Prediction on
Trusted Processors,â€ in Proceedings of ACM Symposium on Cloud Computing
(SoCC), pp. 462â€“476, 2020.

\[21\] A. Biondo, M. Conti, L. Davi, T. Frassetto, and A.-R. Sadeghi,
â€œThe Guardâ€™s Dilemma: Efficient Code-Reuse Attacks Against Intel SGX,â€
in Proceedings of USENIX Security Symposium (USENIX Security), pp.
1213â€“1227, 2018.

\[22\] W. He, S. Guo, S. Guo, X. Qiu, and F. Qi, â€œJoint DNN Partition
Deployment and Resource Allocation for Delay-Sensitive Deep Learning
Inference in IoT,â€ IEEE Internet of Things Journal, vol. 7, no. 10, pp.
9241â€“9254, 2020.

\[23\] T. Mohammed, C. Joe-Wong, R. Babbar, and M. Di Francesco,
â€œDis-tributed Inference Acceleration with Adaptive DNN Partitioning and
Offloading,â€ in Proceedings of IEEE International Conference on
Com-puter Communications (INFOCOM), pp. 854â€“863, 2020.

\[24\] R. Gilad-Bachrach, N. Dowlin, K. Laine, K. Lauter, M. Naehrig,
and J. Wernsing, â€œCryptoNets: Applying Neural Networks to Encrypted Data
with High Throughput and Accuracy,â€ in Proceedings of International
Conference on Machine Learning (ICML), pp. 201â€“210, 2016.

\[25\] G. Lloret-Talavera, M. Jorda, H. Servat, F. Boemer, C. Chauhan,
S. Tomishima, N. N. Shah, and A. J. Pena, â€œEnabling homomorphically
encrypted inference for large dnn models,â€ IEEE Transactions on
Computers (TC), vol. 71, pp. 1145â€“1155, 2021.

\[26\] N. Kumar, M. Rathee, N. Chandran, D. Gupta, A. Rastogi, and R.
Sharma, â€œCrypTFlow: Secure TensorFlow Inference,â€ in Proceedings of IEEE
Symposium on Security and Privacy (S&P), pp. 336â€“353, 2020.

\[27\] A. S. Shamsabadi, A. Gascon, H. Haddadi, and A. Cavallaro,
â€œPrivedge: From Local to Distributed Private Training and Prediction,â€
IEEE Transactions on Information Forensics and Security (TIFS), vol. 15,
pp. 3819â€“3831, 2020.

\[28\] D. L. Quoc, F. Gregor, S. Arnautov, R. Kunkel, P. Bhatotia, and
C. Fet-zer, â€œSECURETF: A Secure TensorFlow Framework,â€ in Proceedings of
International Middleware Conference (Middleware), pp. 44â€“59, 2020.

\[29\] J.-J. Hwang, Y.-C. Chow, F. D. Anger, and C.-Y. Lee, â€œScheduling
Precedence Graphs in Systems with Interprocessor Communication Times,â€
SIAM Journal on Computing, vol. 18, no. 2, pp. 244â€“257, 1989.

\[30\] N. Jafari, O. Selvitopi, and C. Aykanat, â€œFast Shared-memory
Streaming Multilevel Graph Partitioning,â€ Journal of Parallel and
Distributed Computing (JPDC), vol. 147, pp. 140â€“151, 2021.

\[31\] J. Herrmann, J. Kho, B. UcÂ¸ar, K. Kaya, and U. V. CÂ¸atalyurek,
â€œAcyclic partitioning of large directed acyclic graphs,â€ pp. 371â€“380,
2017.

\[32\] E. Bampis and A. V. Kononov, â€œBicriteria Approximation Algorithms
for Scheduling Problems with Communications Delays,â€ Journal of
Scheduling, vol. 8, no. 4, pp. 281â€“294, 2005.

\[33\] D. R. Karger, C. Stein, and J. Wein, â€œScheduling Algorithms,â€ in
Algorithms and Theory of Computation Handbook, ser. Chapman & Hall/CRC
Applied Algorithms and Data Structures series. CRC Press, 1999.

\[34\] J. Hwang, Y. Chow, F. D. Anger, and C. Lee, â€œScheduling
Precedence Graphs in Systems with Interprocessor Communication Times,â€
SIAM Journal on Computing, vol. 18, no. 2, pp. 244â€“257, 1989.

> 644
>
> Authorized licensed use limited to: Universiteit van Amsterdam.
> Downloaded on May 19,2026 at 12:06:17 UTC from IEEE Xplore.
> Restrictions apply.
