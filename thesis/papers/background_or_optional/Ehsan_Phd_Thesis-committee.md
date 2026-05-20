E F F I C I E N T D E E P
L E A R N I N G I N F E R E N C E O N
E N D D E V I C E S

ehsan aghapour

This work was carried out in the ASCI graduate school.
ASCI dissertation series number 468.
Copyright © 2025 Ehsan Aghapour.

Cover Design: from....
Thesis template: classicthesis by André Miede and Ivo Pletikosi´c.
Printed and bound by Ipskamp printing
ISBN: write own ISBN

Advanced School for Computing and ImagingThis work is dedicated to....

A B S T R A C T

Deep Learning (DL) has emerged as a powerful subset of Machine Learn-
ing (ML), particularly for its ability to automatically extract hierarchical
features from large datasets through Deep Neural Networks (DNNs).
This capability has driven advancements across various fields, including
healthcare, computer vision, natural language processing, and autonomous
systems. However, running DL models on resource-constrained end de-
vices, such as smartphones and Internet of Things (IoT) devices, presents
significant challenges due to limitations in computational power, energy
consumption, and latency requirements.

This thesis focuses on addressing the optimization challenges of running
DL inference on Heterogeneous Multi-Processing System-on-Chips (HMP-
SoCs) found in end devices. These systems typically integrate CPU clusters,
GPUs, and Neural Processing Units (NPUs), each offering unique trade-offs
between power efficiency, performance, and accuracy. The research focuses
on the collaborative processor use to improve inference latency, power
efficiency, and throughput. By balancing and optimizing the trade-offs
between accuracy, performance, and power consumption, this work aims
to improve the efficiency of DL models on resource-constrained devices
without significantly compromising the quality of results.
The key contributions of this research are as follows:
Latency Optimization via Layer-Switching Between CPUs and GPUs:
A pre-configured layer-switching strategy is developed, where each layer
of the DL model is assigned to the processor (CPU or GPU) that minimizes
overall inference latency. This method ensures that latency-sensitive appli-
cations, such as Augmented Reality (AR) and Virtual Reality (VR), achieve
the desired performance without compromising real-time responsiveness.
Power Efficiency through Combined DVFS and Layer-Switching: To
address the challenge of power efficiency while meeting latency constraints,
the research employs both Dynamic Voltage and Frequency Scaling (DVFS)
and pre-configured layer-switching between CPUs and GPUs. This ap-
proach optimizes the power consumption of each processor without sacrific-

v

ing performance, ensuring that DL models run within the power constraints
of battery-powered devices while maintaining the desired latency targets.

NPU Integration and Trade-offs Between Accuracy, Power, and Perfor-
mance: NPUs, designed for DL tasks, provide significant gains in power
efficiency and performance, but quantization can introduce accuracy trade-
offs. A selective quantization method is proposed, where only certain
layers are quantized and executed on the NPU, while others retain full
precision. This method balances the competing demands of accuracy, power
consumption, and performance.

Throughput Optimization via Pipelined Execution Across Processors:
To improve throughput, the research introduces a pipelined execution
method that pre-partitions the DL model across CPU clusters, GPUs, and
NPUs. By executing different stages of the model concurrently on different
processors, the system can meet the required Frames Per Second (FPS)
for high-throughput applications like video processing, while maintaining
power efficiency and minimal latency overhead.

Finally, as a significant outcome of this research, we developed and
published ARM-CO-UP, a framework that enable efficient DL inference
on HMPSoCs. This framework offers essential capabilities such as pro-
cessor switching, pipelining, DVFS, and layer-level profiling of execution
time and power consumption. Designed to facilitate cooperative execution
across CPUs, GPUs, and NPUs, ARM-CO-UP is a flexible tool that allows
researchers to experiment with optimizations, switching strategies, and
pipeline execution. Its versatility makes it a valuable contribution to ad-
vancing DL deployment on resource-constrained end devices, supporting
ongoing scientific exploration in this field.

This thesis contributes to the broader goal of deploying advanced Ar-
tificial Intelligence (AI) capabilities on everyday technologies, ensuring
that DL models can run efficiently on resource-constrained devices. The
integrated framework developed here provides a practical and extensible
solution for further exploration in this evolving field.

vi

C O N T E N T S

1

2

3

2

1

4

1

introduction
1.1 Deep Learning
1.2 End Devices and Their Architectures
1.3 Efficient On-Device DL Inference
1.4 Proposed Integrated Framework: ARM-CO-UP
1.5 Thesis Overview
1.6 List of Publications and Author Contributions
1.7 Source Code
background
2.1 Convolutional Neural Networks
2.1.1 CNN General Structure
2.1.2 CNN Layer Types
18
2.1.3 CNN Applications and Architectures

12

16

17

17

17

11

15

21

25

2.2 On-Device Inference

25
2.2.1 Hardware Platform
2.2.2
Software Framework
2.3 Efficiency Aspects of On-Device Inference
2.3.1 Performance-Efficient Inference
2.3.2 Power-Efficient Inference
33
2.3.3 Accuracy Trade-offs

35

29

30

31

2.4 Challenges

36

2.4.1 Technical Challenges
2.4.2 Design and Optimization Challenges

36

37

38

2.5 Summary
layer-switched low latency inference
40
3.1
Introduction
3.2 Related Work
42
3.3 Experimental Setup
3.4 CPU-GPU Layer-Switched Inference With ARM-CL
3.5 Layer Latency Analysis

45

43

39

3.5.1 Effect of Parameters Size on Latency

45

3.6 Results
3.7 Summary

52

52

43

vii

viii

contents

4

5

6

55

69

68

63

64

71

56
60

Implementation

pelsi: power-efficient layer-switched inference
4.1
Introduction
4.2 Related Work
4.3 Setup
61
4.4
4.5 Algorithm
4.6 Results
4.7 Summary
piqi: partially quantized dnn inference on hmp-
socs
5.1
Introduction
5.2 Related Work
5.3
Implementation
5.4 Characterization
5.5 PiQi Framework
81
5.6 Evaluation
84
5.7 Summary
integrated pipeline for high-throughput cnn infer-
ence
6.1
Introduction
6.2 Related Work
6.3 Pipeline Execution
6.4 Methodology

75
77
78

86
89

72
75

85

91

92

6.4.1 Pipe-ALL Framework
6.4.2 CPU-GPU-NPU Pipeline with DVFS

92

94

6.5 Experimental Evaluation

99

6.5.1 Pipe-ALL
99
6.5.2 CPU-GPU-NPU Pipeline and DVFS

101

6.6 Summary

104

7 arm-co-up: arm cooperative utilization of processors

105

7.1
Introduction
7.2 Related Work
7.3 Background
7.4 ARM-CO-UP Framework

106
108

110

114
7.4.1 Co-operative Utilization
7.4.2 Profiling
120
7.4.3 NPU Integration
7.4.4 Power Manager

121
124

114

7.5 ARM-CO-UP Methodology (Workflow)

125

contents

ix

127

7.5.1 Pre-Setup
7.5.2
7.5.3
7.6 Validation

131

Sub-Graph Creation
Sub-Graph Management

127

129

7.6.1 Case Study

131

7.7 Summary
8 conclusion

136
137

8.1 Contributions
8.2 Answers to the Research Questions
8.3 Future Work

141

137

139

bibliography

143

acknowledgements

153

summary

155

samenvatting

157

A C R O N Y M S

ACM Association for Computing Machinery

ARM-CL ARM Compute Library

ASIC Application Specific Integrated Circuit

AI Artificial Intelligence

API Application Programming Interface

AMBA Advanced Microcontroller Bus Architecture

AR Augmented Reality

ARM-CO-UP ARM CO-operative Utilization of Processors

ASCI Advanced School for Computing and Imaging

CCI Cache Coherent Interconnect

CGRA Coarse Grained Reconfigurable Array

CNN Convolutional Neural Network

COCO Common Objects in Context

CPU Central Processing Unit

DL Deep Learning

DNN Deep Neural Networks

DRAM Dynamic Random-Access Memory

DSD Digital System Design

DVFS Dynamic Voltage and Frequency Scaling

EPT Evolutionary Piecemeal Training

x

acronyms

xi

FC Fully Connected

FLOP FLoating-Point OPeration

FPGA Field-Programmable Gate Array

FPS Frames Per Second

GA Genetic Algorithm

GPIO General-Purpose Input/Output

GPU Graphical Processing Unit

HPC High Performance Computing

HMPSoC Heterogeneous Multi-Processing System on Chip

IEEE Institute of Electrical and Electronics Engineers

ILSVRC ImageNet Large Scale Visual Recognition Challenge

IoT Internet of Things

IoU Intersection over Union

ISA Instruction Set Architecture

MAC Multiply Accumulate (arithmatic) operation

mAP mean of Average Precision

MAE Mean Absolute Error

MIT Massachusetts Institute of Technology

ML Machine Learning

NAS Neural Architecture Search

NPU Neural Processing Unit

OpenCL Open Computing Language

ONNX Open Neural Network eXchange framework

OS Operating System

PELSI Power-Efficient Layer-Switched Inference

xii

acronyms

PiQi Partially Quantized DNN Inference on HMPSoCs

PTQ Post-Training Quantization

QAT Quantization-Aware Training

ReLU Rectified Linear Unit

RGB Red Green Blue

RL Reinforcement Learning

SoC System on Chip

SIMD Single Input, Multiple Data

VR Virtual Reality

YOLOv3 You Only Look Once, version 3

1

I N T R O D U C T I O N

AI and ML have undergone significant advances in recent years, becoming
integral to numerous societal applications—from healthcare diagnostics to
financial forecasting. Among these developments, DL stands out for its
ability to detect and interpret intricate patterns in data, facilitating break-
throughs in computer vision, natural language processing, and beyond.

1.1 deep learning

DL is a rapidly evolving subset of AI and ML, characterized by its ability
to automatically learn hierarchical representations of data through DNNs.
Unlike traditional ML models, which often require handcrafted features,
DL models are capable of automatically discovering intricate structures in
large datasets, making them particularly effective for complex tasks such
as image and speech recognition [1]. At the core of these models is a multi-
layered architecture, where nonlinear processing units transform raw input
data into progressively higher-level representations.

Among the various DL architectures, CNNs have emerged as a dominant
approach for processing spatial data such as images and videos. CNNs
leverage convolutional layers to automatically extract hierarchical features
from input data, followed by pooling layers that reduce dimensionality,
making them highly efficient for tasks like image classification and object
detection [2]. CNNs are a central focus in this thesis, serving as the primary
benchmark for evaluating our techniques and optimizations.

To develop and deploy DL models effectively, they undergo a compu-
tational pipeline consisting of a learning phase, where they extract pat-
terns from vast datasets, and a deployment phase, where they apply this
learned knowledge to new input data. The initial learning process, known
as training, is computationally intensive and requires high-performance
servers equipped with specialized hardware such as GPUs. Once trained,

1

2

introduction

the model transitions to deployment, performing inference to generate pre-
dictions. While inference generally requires fewer computational resources
than training, it still presents challenges for real-time applications.

Although cloud-based inference has traditionally been the standard
for executing DL models, it introduces key limitations, including latency,
privacy risks, and dependence on network connectivity. Sending data to
remote servers can delay real-time applications, while transmitting sensitive
user information increases security concerns. Moreover, reliable network
access is not always guaranteed, making cloud-based inference impractical
for applications that require immediate decision-making or operate in
bandwidth-limited environments. Therefore, there is growing interest in
performing inference directly on end devices.

By eliminating reliance on external servers, on-device inference reduces
latency, ensuring faster response times for autonomous vehicles, drones, AR
systems, and interactive AI assistants, where even slight delays can degrade
performance or compromise safety. It also enhances privacy by keeping
sensitive data on the user’s device, a crucial factor in health-monitoring
applications that process personal medical data. Additionally, bandwidth
efficiency improves as on-device inference minimizes data transmission,
making it particularly valuable for mobile and remote applications that
must function reliably even with limited or intermittent connectivity.

1.2

end devices and their architectures

Modern end devices integrate multiple processing units within a SoC to
balance performance and power efficiency. The CPU serves as the general-
purpose core of these devices, often designed with heterogeneous architec-
tures such as ARM’s big.LITTLE, which pairs high-performance (big) cores
with energy-efficient (LITTLE) cores to dynamically manage workloads and
optimize battery life [2]. In such architectures, these groups of big and
LITTLE cores form what is commonly referred to as CPU clusters, with
each cluster designed to handle different levels of computational demand.
While CPUs are versatile, they alone are often insufficient for efficiently
handling the growing computational demands of DL workloads.

To complement CPUs, many end devices incorporate GPUs that support
parallel data processing, making them suitable for accelerating DL tasks
such as CNNs for image recognition [3]. However, unlike HPC GPUs in
server-grade systems, embedded GPUs in end devices often have process-
ing power comparable to CPUs. In some cases, depending on the model

1.2 end devices and their architectures

3

architecture and hardware constraints, CPUs may even outperform GPUs.
This makes it essential to carefully evaluate the role of both processors
when deploying DL models. Efficient workload distribution between CPUs
and GPUs is therefore crucial to achieving optimal performance while
adhering to energy and thermal constraints.

In recent years, high-end end devices have begun incorporating dedi-
cated NPUs to further enhance on-device AI processing. These specialized
accelerators are optimized for matrix operations central to DL inference,
often employing lower-precision computations such as quantization to
improve efficiency. While NPUs are not yet standard across all end devices,
their growing presence underscores the increasing shift toward dedicated
AI hardware for real-time, low-latency inference [4].

Although end devices have significantly improved in processing capa-
bilities, they remain constrained in comparison to desktop or cloud plat-
forms, particularly in terms of computational power, memory, and energy
availability [3, 5]. Running DL models on such devices is particularly chal-
lenging because these workloads demand intensive matrix computations,
requiring high processing throughput while operating within a limited
power budget. For instance, widely used CNNs such as ResNet-50 require
billions of FLOPs—about 4 GigaFLOPs—per inference, making execution
on low-power embedded processors difficult. Additionally, modern DL
models often require hundreds of megabytes of memory to store weights
and activations, further straining devices with limited main memory and
cache. Unlike cloud-based servers, which can leverage dedicated accelera-
tors with ample power and cooling, end devices must balance performance
with battery consumption to ensure sustained operation [5].

Moreover, deploying DL inference on end devices requires addressing
real-time processing demands while balancing energy efficiency. One of
the primary motivations for performing inference locally rather than re-
lying on cloud-based methods is to reduce communication delays and
enhance responsiveness. However, achieving low-latency inference remains
a challenge due to the computational burden of DL models. Unlike cloud
environments, where high-performance GPUs and dedicated accelerators
can process inference efficiently, end devices must intelligently distribute
workloads across available processing units—including CPUs, GPUs, and,
when available, NPUs—to optimize energy consumption while maintaining
acceptable response times.

Another critical aspect is the heterogeneous nature of end-device ar-
chitectures. While server environments feature powerful GPUs capable

4

introduction

of handling DL workloads independently, the scenario on end devices is
fundamentally different. GPUs in these devices are considerably weaker,
with computational power often comparable to CPU clusters. This makes it
essential to design inference strategies that leverage all available hardware
resources effectively. Current DL frameworks primarily optimize execution
for either CPUs or GPUs but often lack efficient mechanisms for utilizing
both simultaneously, limiting their applicability in HMPSoCs. Given the
constrained processing power of these devices, a synergistic approach
that dynamically distributes workloads across CPUs, GPUs, and NPUs is
necessary to meet the growing performance demands of DL workloads.

1.3

efficient on-device dl inference

While DL models continue to improve in accuracy and expand in capa-
bilities, these advancements come at the cost of exponentially increasing
computational and energy requirements. State-of-the-art architectures, such
as large-scale CNNs, require billions of parameters and immense process-
ing power, further exacerbating the challenge of deploying them efficiently
on resource-constrained end devices. Unlike cloud-based servers, where
ample computational resources can be leveraged, end devices must operate
within strict power and memory constraints, requiring careful optimization
strategies to ensure inference.

Deploying DL models efficiently on such devices requires specialized
optimizations, from model compression techniques to efficient hardware
utilization strategies, ensuring that inference remains both feasible and
effective in real-world conditions. The increasing computational and en-
ergy demands of modern DL models underscore the urgency of devel-
oping novel methods for optimizing inference performance on resource-
constrained devices. Given these challenges and the increasing demand
for efficient DL inference on end devices, particularly in the context of
HMPSoCs found in modern smartphones, this thesis seeks to address
several key research questions. Each question targets a specific aspect of
optimizing DL model latency, performance, power efficiency, and accuracy
within resource-constrained environments.

RQ1: Given the critical role of responsiveness in real-time applications, what
strategies can be employed to minimize inference latency on conventional HMP-
SoCs equipped with CPUs and GPUs?

1.3 efficient on-device dl inference

5

LITTLE CPU Cluster

big CPU Cluster GPU

]
s

m

[

y
c
n
e
t
a
L

600

400

200

0

AlexNet

GoogleNet

MobileNet

ResNet50

SqueezeNet

Figure 1.1: The inference latency for different inference capable components for

different CNNs on Khadas Vim 3.

Motivation: Latency is a critical factor in many HMPSoC applications.
Inference latency on the big CPU and GPU is often comparable, making
processor selection for latency optimization non-trivial, as illustrated in
Figure 1.1. While GPUs are generally well-suited for parallel computations,
certain DL layers may execute just as efficiently—or even faster—on the
big CPU, depending on their computational characteristics. However, dis-
tributing layer execution across multiple processors introduces communi-
cation overhead, which can offset potential performance gains. Therefore,
an workload allocation strategy that minimizes inter-processor switching
while leveraging the strengths of both the big CPU and GPU is essential for
achieving low-latency inference in real-time applications.

Approach: To address this challenge, in Chapter 3, we focus on develop-
ing a framework that supports dynamic switching between CPU clusters
and GPUs during DL model inference. This strategy enables the most
appropriate processor to handle each layer of the model, ensuring that the
processor best suited for the task is utilized. The key steps involved are:

1. Processor Integration and Switching: The first challenge is enabling
both the CPU and GPU to work together within a single inference
task, rather than choosing one or the other. Existing tools typically
allow selecting either CPU or GPU for inference but not both for a
single task. The framework developed in this research splits the model
graph into sub-graphs that are assigned to different processors (CPU
or GPU), ensuring proper synchronization and data communication.

2. Layer-Wise Processor Switching: By analyzing the performance of
various CNN layers—taking into account parameters such as layer
type, input shape, and number of filters—this research identifies
which layers perform more efficiently on CPUs versus GPUs. Based
on this analysis, the framework implements a layer-switching strategy,

6

introduction

assigning layers to the processor that can execute them with the
least latency. The framework also includes profiling tools to measure
latency per layer on each processor. This data allows for an optimized
setup of layer-to-processor assignments, ensuring minimal switching
overhead and efficient data transfers.

Outcomes: The implemented layer-switching strategy demonstrates re-
ductions in inference latency for CNNs running on HMPSoCs, despite the
switching overhead and data transfers between processors. This research
contributes to a deeper understanding of how different processors handle
various DL layers, increasing efficiency in latency-sensitive applications.

RQ2: How can we optimize inference power efficiency while meeting target

latency requirements on HMPSoCs?

Motivation: Power efficiency is critical for embedded devices, which of-
ten rely on battery power for extended periods. However, optimizing power
consumption must not come at the expense of performance, especially
in latency-sensitive applications. The challenge is to balance the power
efficiency and performance to ensure efficient DL model execution without
compromising device autonomy or exceeding latency constraints.

Approach: Chapter 4 introduces several following strategies and opti-
mizations aimed at improving power efficiency while meeting performance.

1. DVFS: DVFS is employed to adjust the power consumption of CPU
clusters and GPUs based on the computational workload. By fine-
tuning the voltage and frequency for each processor, the framework
seeks optimal trade-off between power consumption and latency.

2. Layer-Specific DVFS Tuning: Recognizing that different DL model
layers have varying computational demands, DVFS settings are tuned
on a per-layer basis. This design ensures that each layer executes
power efficienctly while still meeting end-to-end latency constraints.

3. GA for Optimization: A GA is used to explore the vast design space
of possible layer mappings and DVFS configurations. This exploration
allows the framework to identify optimal settings for power efficiency
without sacrificing performance.

4. Power and Performance Prediction Models: A profile-based pre-
diction model is developed to estimate the end-to-end latency and

1.3 efficient on-device dl inference

7

power consumption for different configurations. This allows the GA
to efficiently search the design space, identifying configurations that
meet latency constraints while optimizing power efficiency.

Outcomes: The proposed methods demonstrate improvements in power
efficiency without violating the desired latency targets. This approach pro-
vides a practical solution for balancing power and latency in DL inference
on HMPSoCs, making it applicable across a variety of end devices.

RQ3: How can emerging neural network accelerators (e.g., NPUs) be leveraged
to explore accuracy-performance-power trade-offs and find the optimal balance for
target accuracy in end devices?

Motivation: Recent devices integrate NPUs, which are specialized accel-
erators designed for DL tasks. NPUs offer substantial improvements in
performance and power efficiency, particularly when running quantized
models. However, quantization can lead to accuracy losses, which is a
critical drawback for applications where precision is essential. Thus, the
challenge is to explore how NPUs can be used to strike the best balance
between performance, power efficiency, and accuracy.

Approach: Chapter 5 introduces and evaluates the following strategies to

enhance power efficiency while maintaining accuracy and performance:

1. Partial Quantization: Instead of fully quantizing a DL model, the
research selectively quantizes layers that contribute less to overall
model accuracy while providing significant power and performance
gains. These layers are assigned to the NPU, while more critical layers
remain in full precision and are handled by the CPU or GPU.

2. PiQi Framework: The PiQi framework is developed to support partial
quantization and dynamic layer-switching between CPUs, GPUs, and
NPUs. Incorporating NPUs into this framework presents technical
challenges, given the distinct execution contexts between NPUs and
conventional processors. The framework addresses these challenges,
enabling cooperative execution between NPUs, CPUs, and GPUs in
switch mode. Additionally, the PiQi framework uses a multi-objective
GA and per-layer DVFS tuning to optimize the trade-offs between
power, performance, and accuracy.

3. Accuracy Prediction Model: To expedite the search for optimal con-
figurations, the research develops a neural network-based accuracy

8

introduction

LITTLE CPU big CPU GPU NPU (Non-Quantized)

]
S
P
F
[

t
u
p
h
g
u
o
r
h
T

40

30

20

10

0

AlexNet

GoogleNet

MobileNet

ResNet50

SqueezeNet

Figure 1.2: Single processor inference throughput of CPU clusters, GPU, and NPU

on RockPi N10

prediction model. This model predicts the accuracy impact of quan-
tizing specific layers, allowing the GA to efficiently explore the design
space and identify configurations that meet the accuracy constraints
while optimizing for power and performance.

Outcomes: The PiQi framework and the associated strategies demon-
strate that NPUs can be leveraged effectively to achieve high performance
and power efficiency without significant accuracy loss. This research pro-
vides insights into how to best utilize NPUs in conjunction with CPUs and
GPUs, offering a solution for deploying DL models on end devices.

RQ4: How can we improve inference throughput and power efficiency with

minimal latency overhead in HMPSoCs?

Motivation: In the previous research questions, we focus on minimizing
inference latency in DL models running on HMPSoCs. However, as DL
applications evolve, meeting real-time performance demands requires not
only low latency but also high throughput. Many applications, such as
video processing and real-time analytics, require sustaining a high FPS to
avoid performance degradation. If the system fails to maintain the required
throughput, buffering, queuing, or even data overflow can occur, leading to
increased latency and reduced system responsiveness.

While AR and VR applications are highly latency-sensitive—where even
minor delays can disrupt user experience—other workloads, like video
streaming, real-time object detection, and large-scale multi-camera systems,
are also throughput-sensitive, requiring sustained high FPS to maintain
smooth operation. Thus, optimizing for throughput is critical to ensure
system stability while also maintaining low latency where necessary.

1.3 efficient on-device dl inference

9

Evaluations show that single-processor inference is insufficient to meet
the demands of modern DL applications. Figure 1.2 highlights the inference
throughput of different processors when running conventional CNNs. Un-
like non-embedded systems, where GPUs significantly outperform CPUs,
the performance of CPUs and GPUs in HMPSoCs is often comparable,
;eading to inefficiencies when using these processors in isolation.

In addition to meeting the required FPS, improving throughput can
enhance power efficiency. Parallel execution across processors—such as
cooperative execution of CPU clusters and GPUs—reduces overall inference
time, leading to better utilization of system resources. This execution results
in improved energy efficiency, as processors are active for shorter periods,
and idle components (along with other parts of the SoC) consume less
power. Therefore, parallel execution not only ensures real-time performance
but also contributes to power-efficient operation.

For this purpose, Chapter 6 first focuses on optimizing pipeline execution
across the LITTLE CPU, big CPU, and GPU, as these processors are widely
available in most end devices. After achieving higher throughput with
minimal latency overhead using these common processors, we extend the
optimization by incorporating NPUs—power-efficient processors in mod-
ern SoCs—and introducing DVFS to further reduce power consumption.
The addition of NPUs enables deeper optimization strategies aimed at
enhancing both throughput and power efficiency.

Approach: In Chapter 6, this research tackles the challenge of improving
inference throughput and power efficiency through pipelined execution
across CPU clusters, GPUs, and NPUs. The approach is structured into two
phases, with additional optimization strategies applied within each phase:

1. Phase 1: CPU-GPU Pipeline Execution – The initial focus is on
improving throughput by implementing pipelined execution across
the LITTLE CPU, big CPU, and GPU. The DL model is divided into
stages, with each processor handling a different stage. By processing
consecutive frames in a pipeline, these processors work concurrently,
helping to meet the required throughput for modern applications.
The key advantage of pipelining is minimizing communication over-
head between processors. Instead of parallelizing every layer across
all processors—which would introduce significant data transfer de-
lays—pipelining allows each processor to focus on a specific stage.
This reduces synchronization issues, maximizes processor utilization,
and ultimately boosts throughput while maintaining a proper balance
between throughput and latency.

10

introduction

challenges in pipeline execution A key challenge in this
phase is ensuring smooth synchronization and communication be-
tween pipeline stages. Unlike the processor switching (serial mode)
discussed in previous research questions, pipeline execution involves
concurrently processing different model stages. This execution re-
quires managing buffering between stages to ensure that processors
do not stall while waiting for data from preceding stages. Addi-
tionally, synchronization mechanisms must minimize inter-processor
communication overhead and balance workloads across the pipeline
to prevent any processor from becoming a bottleneck. Efficiently
managing these aspects is essential to maintaining high throughput
with minimal latency overhead.

2. Phase 2: Incorporating NPUs and DVFS for Power Efficiency –
After optimizing pipeline execution across CPU clusters and GPUs,
we extend the pipeline to incorporate NPUs. By adding the NPU,
we offload the majority of DL operations to this power-efficient
processor while running specific layers in CPU and GPU in parallel
within the pipeline, further improving both throughput and power
efficiency. Since NPUs are highly optimized for DL tasks, their inclu-
sion significantly boosts performance and energy efficiency. Along-
side integrating the NPU, we apply DVFS to the CPU clusters and
GPU, dynamically adjusting power consumption based on workload
demands. This ensures that power is consumed efficiently without
compromising throughput.

exploration of configurations using a multi-objective
ga Given the complexity of optimizing pipeline execution, parti-
tioning the model, assigning processors, and tuning DVFS settings,
a multi-objective GA is employed as an optimization strategy in
this phase. The GA helps identify configurations that optimize both
throughput and power efficiency by evaluating different partition-
ing schemes, processor assignments, and DVFS settings. During the
GA search, the framework evaluates each configuration by running
the model in real-time, measuring both throughput and power con-
sumption. Automated evaluation mechanisms streamline this process,
allowing the GA to efficiently explore optimal configurations that
balance throughput and energy consumption, ultimately leading to
a Pareto-optimal set of solutions.

1.4 proposed integrated framework: arm-co-up

11

Outcomes: The results in Chapter 6 demonstrate that pipelined execution
across CPU clusters and GPUs significantly improves inference through-
put while maintaining minimal latency overhead. By incorporating NPUs
and applying DVFS settings, the pipeline execution achieves even greater
gains in both throughput and power efficiency, making the framework
more suitable for modern real-time applications. The multi-objective GA
effectively identifies configurations that optimize throughput and power ef-
ficiency, providing a robust solution for real-time DL inference on resource-
constrained devices. These findings offer best practices for pipeline config-
uration and processor utilization in HMPSoCs, contributing to the broader
goal of efficient DL deployment on end devices.

1.4

proposed integrated framework: arm-co-up

During the course of this Ph.D. research, several specialized frameworks
were developed, each designed to address specific challenges such as
processor switching, pipeline execution, power management, per-layer pro-
filing, etc., in HMPSoCs. While these individual frameworks are effective
in their respective domains, the need for a unified solution becomes in-
creasingly clear. The motivation behind creating an integrated framework,
ARM-CO-UP, stems from the desire to simplify the process of running DL
inference collaboratively across multiple processors and to offer a valuable
resource to the research community. The significant investment of time and
effort in designing and implementing these frameworks naturally motivates
the development of a comprehensive tool to maximize the impact.

ARM-CO-UP is a unified framework that facilitates the cooperative exe-
cution of HMPSoC processors, including CPU clusters, GPUs, and NPUs,
in both pipeline and switching modes. This framework addresses the gap
in existing tools by providing seamless cooperative execution of DL models
on these devices. In addition to this core functionality, ARM-CO-UP offers
several advanced features, such as profiling execution time and power
consumption at the granularity of individual layers. The framework also
integrates a power manager that allows for power-efficient execution of
DL models on CPU and GPU processors. Chapter 7 further elaborates the
details and features of the framework.

This integrated framework is not simply a collection of previous work

but a redesigned and enhanced system that offers significant benefits:

Unified Access: ARM-CO-UP consolidates the features of separate frame-
works into a single, cohesive tool that can handle a wide range of tasks. This

12

introduction

unification eliminates the need to switch between different frameworks and
repositories, streamlining workflows for researchers and practitioners.

Ease of Use: Designed with user-friendliness in mind, ARM-CO-UP al-
lows researchers to run inference with their desired configurations through
straightforward command-line commands. This simplicity removes the
need for users to engage with the complexities of the underlying imple-
mentation, making the framework accessible to a broader audience.

Extensibility: Previously, adding new DL models required custom im-
plementation work. ARM-CO-UP addresses this by centralizing the model-
splitting mechanism, enabling automatic handling of model partitioning
and communication. This centralization makes the framework adaptable to
emerging research needs, allowing new DL models to be integrated.

Standardization and Generalization: The framework’s redesign includes
the standardization of new features into extended classes, easing the mi-
gration to future versions. ARM-CO-UP also supports the addition of new
NPUs and accelerators with minimal effort, ensuring the framework can
accommodate a wide variety of hardware setups.

The development of ARM-CO-UP as part of this thesis work was driven
by the goal of creating a resource that not only supports the research as
presented in this thesis but also provides lasting value to other researchers
and practitioners. The framework is made publicly available under the MIT
license, encouraging further adoption and development.

1.5

thesis overview

This thesis is structured into several key chapters, each building upon the
previous one to address the complex challenges of running DL models on
resource-constrained end devices. The chapters are designed to progres-
sively tackle the various aspects of DL inference, including performance
optimization, power efficiency, and accuracy, culminating in the develop-
ment of a unified framework for cooperative execution across HMPSoCs.
Below is an extended overview of the thesis structure:

Chapter 2: Background The second chapter provides foundational back-
ground on DL models, their evolution, architectures, and the challenges
of deploying them on resource-constrained devices. It covers the structure
of CNNs, explaining their layers, followed by their applications in object
classification and detection. The discussion then transitions to on-device in-
ference, introducing the common hardware architectures used for DL, such
as CPUs, GPUs, and NPUs, and examining how software frameworks are

1.5 thesis overview

13

designed to utilize these platforms for efficient inference. It highlights the
specifications of these frameworks, their design considerations, and their
limitations in executing DL workloads on HMPSoCs. Additionally, it ex-
amines key efficiency aspects, including performance, power consumption,
and accuracy metrics. The goal is to establish a solid technical foundation
and context for the research presented in subsequent chapters.

Chapter 3: Latency Optimization Through CPU/GPU Switching This
chapter focuses on optimizing inference latency, a critical metric for real-
time applications. It presents a methodology that dynamically switches
between CPU and GPU execution based on the characteristics of different
layers within a DL model. The chapter gives an in-depth analysis of the
performance characteristics of CPU and GPU processors for various DNN
layers, identifying conditions where each processor performs optimally.
Based on this analysis, a layer-wise switching strategy is introduced to
improve inference efficiency by selecting the most suitable processor for
each layer. The methodology is evaluated to demonstrate its effectiveness
in reducing latency on HMPSoCs, providing insights into how processor
selection impacts DL inference latency.

Chapter 4: Power Efficiency Optimization with DVFS This chapter
focuses on optimizing the power efficiency of DL inference on HMPSoCs
while maintaining specific latency constraints. It builds upon the latency
optimization strategies introduced in the previous chapter by incorporating
DVFS as a means to reduce power while ensuring latency targets are met.
The chapter examines how different layers of a DL model can benefit from
tailored DVFS settings based on their computational characteristics. A GA
is employed to navigate the extensive design space of possible configura-
tions, identifying power-efficient settings that meet latency requirements.
The findings provide practical guidelines for balancing power efficiency
and performance in DL inference on mobile and embedded devices.

Chapter 5: NPU Integration and Accuracy-Power-Performance Trade-
offs This chapter extends the work on latency and power efficiency by intro-
ducing the NPU into the optimization process. NPUs, designed specifically
for executing DL tasks, offer significant performance and power efficiency
gains but come with the potential drawback of reduced accuracy due to
quantization. Therefore, this chapter investigates the accuracy-performance
trade-offs when utilizing NPUs in HMPSoCs. It introduces a novel method-
ology for partial quantization, where certain layers of the DL model are
quantized and executed on the NPU, while others remain in full precision
and are processed by the CPU or GPU. The goal is to achieve the best

14

introduction

possible performance and power efficiency while maintaining acceptable
accuracy levels. The chapter shows the use of a multi-objective GA to
find the optimal balance between these competing factors, providing a
comprehensive solution for deploying DL models on end devices.

Chapter 6: Enhancing Throughput with CPU/GPU and CPU/GPU/NPU
Pipelines This chapter shifts the focus from latency optimization to improv-
ing inference throughput on HMPSoCs. It explores pipelining techniques
to distribute inference tasks across multiple processors within the SoC,
initially focusing on CPU clusters and GPU. The primary objective is to
maximize FPS while minimizing latency overhead. The chapter introduces
a pipeline-based execution strategy for DL inference on ARM HMPSoCs,
where the workload is distributed across big and LITTLE CPUs and the
GPU. This requires careful partitioning of the DL model and efficient
management of inter-processor communication to minimize overhead. The
pipeline is then extended to incorporate the NPU, further improving in-
ference efficiency. Additionally, a design space exploration is conducted
to optimize throughput and energy efficiency by integrating DVFS for
each processor. The results show pipeline execution strategies, processor
selection, and adaptive power management can improve DL inference.

Chapter 7: ARM-CO-UP: A Unified Framework for Cooperative Exe-
cution The final chapter introduces the ARM-CO-UP framework, which
represents the culmination of the various features developed throughout
this research. ARM-CO-UP is a unified tool designed to support cooperative
and efficient execution across all major processors in HMPSoCs, including
CPU clusters, GPUs, and NPUs. This chapter explains how the framework
integrates the specialized features implemented in earlier chapters—such as
pipeline and switching modes, layer-level profiling of execution time and
power consumption, and an integrated power manager—into a comprehen-
sive system. These features, which are foundational to the methodologies
proposed in this thesis, are now brought together in a cohesive framework
that simplifies the execution of DL models on end devices. The chapter also
discusses the framework’s extensibility and its potential to impact future
research and development in DL.

Chapters 3 to 7 present the core contributions of this thesis, addressing
key challenges in optimizing DL inference on resource-constrained end
devices. The thesis concludes with Chapter 8, where we reflect on the
research questions and discuss potential directions for future research.

1.6 list of publications and author contributions

15

1.6

list of publications and author contributions

This section outlines the relationship between each paper and the research
chapters, along with a summary of my contributions.

Ch.3

[P1] CPU-GPU Layer-Switched Low Latency CNN Inference
E. Aghapour, D. Sapra, A. Pimentel, A. Pathania.
2022 25th Euromicro Conference on Digital System Design (DSD), pp.
324-331, IEEE, 2022.

E.A. is the principal author and was responsible for designing, imple-
menting, and validating the proposed methods, and performing all
experiments, conducting data analysis, and developing the software.
E.A. was also the person responsible for writing the manuscript.

Ch.4

[P2] PELSI: Power-Efficient Layer-Switched Inference
E. Aghapour, D. Sapra, A.D. Pimentel, A. Pathania.
2023 IEEE 29th International Conference on Embedded and Real-Time
Computing Systems and Applications (RTCSA), pp. 12-17, IEEE, 2023.

E.A. is the principal author and was responsible for designing, imple-
menting, and validating the proposed methods, and performing all
experiments, conducting data analysis, and developing the software.
E.A. was also the person responsible for writing the manuscript.

Ch.5

[P3] PiQi: Partially Quantized DNN Inference on HMPSoCs
E. Aghapour, Y. Shen, D. Sapra, A. Pimentel, A. Pathania.
Proceedings of the 29th ACM/IEEE International Symposium on Low
Power Electronics and Design (ISLPED), pp. 1-6, ACM/IEEE, 2024.

E.A. is the principal author and was responsible for designing, imple-
menting, and validating the proposed methods, and performing all
experiments, conducting data analysis, and developing the software.
E.A. was also the person responsible for writing the manuscript.

Ch.6

[P4] Pipelined CNN Inference on Heterogeneous Multi-processor System-
on-Chip
E. Aghapour, Y. Zhang, A. Pathania, T. Mitra.
In Embedded Machine Learning for Cyber-Physical, IoT, and Edge Com-
puting: Software Optimizations and Hardware/Software Codesign, pp. 405-
427, Springer, 2023.

16

introduction

E.A. is the principal author and was responsible for designing, imple-
menting, and validating the proposed methods, and performing all
experiments, conducting data analysis, and developing the software.
E.A. collaboratively wrote the manuscript with the supervisor.
[P5] Integrated ARM big.LITTLE-Mali Pipeline for High-Throughput
CNN Inference
E. Aghapour, A. Pathania, G. Ananthanarayanan.
Authorea Preprints, Authorea, 2023.

E.A. is the principal author and was responsible for designing, imple-
menting, and validating the proposed methods, and performing all
experiments, conducting data analysis, and developing the software.
E.A. collaboratively wrote the manuscript with the supervisor.

Ch.7

[P6] ARM-CO-UP: ARM COoperative Utilization of Processors
E. Aghapour, D. Sapra, A. Pimentel, A. Pathania.
ACM Transactions on Design Automation of Electronic Systems, ACM,
New York, NY, 2024.

E.A. is the principal author and was responsible for designing, imple-
menting, and validating the proposed methods, and performing all
experiments, conducting data analysis, and developing the software.
E.A. was also the person responsible for writing the manuscript.

1.7

source code

The implementations and frameworks developed as part of this research are
publicly available under open-source licenses. Below are the repositories
corresponding to different chapters of this thesis:

• CPU-GPU Layer-Switched Inference (Chapter 3):

https://github.com/Ehsan-aghapour/ARMCL-pipe-all/tree/n-pipe-1

• PELSI: Power-Efficient Layer-Switched Inference (Chapter 4):

https://github.com/Ehsan-aghapour/ARMCL-pipe-all/tree/CPU-GPU-LW

• PiQi: Partial Quantization for Heterogeneous Inference (Chapter 5):

https://github.com/Ehsan-aghapour/PiQi

• Pipe-All: Pipelined Execution for Multi-Processor Inference (Chapter 6):

https://github.com/Ehsan-aghapour/ARMCL-Pipe-All

• ARM-CO-UP Framework (Chapter 7):

https://github.com/Ehsan-aghapour/ARM-CO-UP

All repositories are licensed under the MIT license to facilitate repro-
ducibility and further research in DL inference optimization on HMPSoCs.

2

B A C K G R O U N D

In this chapter, we present the foundational concepts and survey the exist-
ing literature that underpins this thesis. We introduce CNNs, which serve
as the primary computational workload in our research. We then delve into
on-device DL, discussing the hardware platforms and software frameworks
for running DL models on end devices. Next, we explore the background
efficiency aspects of on-device inference, focusing on performance, power,
accuracy considerations, and associated challenges.

2.1 convolutional neural networks

CNNs are considered as one of the most widely used class of DL models,
especially in vision-related applications. CNNs can learn representations
from the grid-like data, and recently it has shown substantial performance
improvement in various ML applications. The hierarchical feature extrac-
tion ability of CNNs emulates the deep and layered learning process of the
neocortex in the human brain, which dynamically learns features from the
raw data [6]. By automating feature extraction, CNNs eliminate the need
for manual feature engineering [7] and can efficiently learn representations
directly from raw pixel data. Key characteristics of CNNs include hier-
archical learning, automatic feature extraction, multi-tasking, and weight
sharing [8]. They are particularly well-suited for tasks such as image
classification, object detection, and semantic segmentation. In this section,
we provide an overview of CNNs, discuss their internal architecture, and
define key concepts pertinent to our research.

2.1.1 CNN General Structure

A CNN typically consists of an input layer, multiple hidden layers, and an
output layer. The hidden layers include convolutional layers, pooling layers,

17

18

background

activation functions, and fully connected layers. The general structure can
be divided into two main stages:

• Feature Extraction: Performed by convolutional layers, normalization
layers, and pooling layers, this stage extracts meaningful features
from the input data by applying convolution operations with learned
kernels and refining feature representations through normalization
and downsampling.

• Classification: Implemented through fully connected layers, this stage
takes the extracted features and maps them to the final predictions,
such as class labels or other task-specific outputs.

Understanding how these layers interact in the feature extraction and
classification process is crucial, as they directly impact the computational
characteristics of CNNs, particularly in optimizing DL inference.

2.1.2 CNN Layer Types

Each layer type in a CNN plays a specific role in data processing and
significantly impacts performance metrics like latency and throughput.

2.1.2.1 Convolutional Layers

Convolutional layers are the core building blocks of CNNs. They apply
convolution operations to the input data using a set of learnable filters or
kernels. Each filter slides over the input feature map to produce an output
feature map, capturing spatial hierarchies and patterns.

The input to a convolutional layer is a tensor of shape (Hin × Win × Cin),
where Hin and Win are the input height and width, and Cin is the number
of input channels. The filters are tensors of shape (Kh × Kw × Cin), where
Kh and Kw are the kernel height and width. The output is a tensor of shape
(Hout × Wout × Cout), where Cout is the number of filters applied.

Figure 2.1 illustrates the input data structure and filters for a convolution
layer. This layer has two filters and generates two channels for the output
tensor. The number of kernels in each filter equals the number of input
channels and is three for this example layer. The shape of each output
channel (output height and output width) depends on the shape of the
input and kernel, stride, and padding. Due to weight sharing ability of
convolutional operation, different sets of features within an image can be

2.1 convolutional neural networks

19

Input

5 6 3 4 2 1

0 4 0 0 5 9

6 0 7 5 4 9

5 9 3 3 7 8

5 5 8 7 2 3

0 7 4 7 7 7

7 0 1 2 5 2

6 1 0 2 4 7

5 0 4 7 1 3

6 1 3 9 1 7

8 3 1 1 1 1

5 0 3 7 2 5

9 3 9 1 2 5

5 5 1 6 2 5

1 8 3 5 7 8

8 0 5 1 7 5

4 7 3 5 1 0

7 7 6 2 7 6

6
=
H

Filter 1
1 2 5

0 6 2

4 1 0

3 5 8

2 4 5

7 7 8

6 2 0

3 4 6

1 3 4

3 × 3 × 3

*

Filter 2
6 0 9

3 6 5

6 3 8

7 7 8

4 5 7

5 8 9

9 7 1

0 4 3

2 9 9

C = 3

W = 6

6 × 6 × 3

3 × 3 × 3

4 × 4

4 × 4

=

=

Output

4 × 4 × 2

Figure 2.1: Data structure for a convolution layer. This layer has an input tensor
with three channels. It has two filters processing the input tensor,
producing two channels of the output tensor.

extracted by sliding kernel with the same set of weights on the image and
thus makes CNN parameter efficient versus the fully connected networks.

2.1.2.2 Activation Functions

The outputs generated by the convolutional kernels are passed through
activation functions, which introduce non-linearity into the feature space
and enable the network to learn abstract representations and complex
patterns. The ReLU [9] and its improvements are almost the most popular
activation functions used in DNNs. ReLU involves only simple element-
wise comparisons, making it lightweight in both computation and commu-
nication costs, versus the more resource-intensive convolutional layers.

2.1.2.3 Pooling Layers

Features extracted by convolution can appear at different locations in
an image. However, once extracted, their precise position becomes less
critical as long as their relative arrangement is preserved. Pooling or down-
sampling is an interesting local operation. It sums up similar information in
the neighborhood of the receptive field and outputs the dominant response
within this local region [10]. Pooling layers reduce the spatial dimensions
of feature maps, decreasing the data size and thus reducing computational
complexity and memory requirements. This downsampling also aids in
controlling overfitting by retaining essential features while discarding un-
necessary details. Common pooling operations include max pooling, which
selects the maximum value in a region, and average pooling, which com-

20

background

Weights Matrix

f

Input Vector

5 6 3 4 2 1 5 9 3

.

1 × 9

3 7 8 7

0 1 2 5

2 6 1 3

9 1 7 9

3 9 1 2

5 8 0 5

1 7 5 0

4 0 0 5

9 5 5 8

9 × 4

Output Vector
=

A B C D

1 × 4

Figure 2.2: Data structure for a fully-connected layer. This layer has a flattened
input tensor (one dimension). The weight tensor is a 2D tensor with
the shape: (input_size) × (number_of_neurons). The output is a flat
tensor with a size of (number_of_neurons).

putes the average value. Both operations are relatively lightweight, as they
involve simple aggregation over small regions, making them significantly
less demanding compared to convolutional layers.

2.1.2.4 Normalization Layers

Normalization layers, such as Batch Normalization [11], standardize the
inputs to a layer for each mini-batch, stabilizing the learning process and
improving convergence speed. Batch normalization unifies the distribution
of feature-map values by setting them to zero mean and unit variance.
Efficient implementation of normalization layers is important for maintain-
ing inference speed on end devices. The number of operations required is
relatively small compared to convolutional layers.

2.1.2.5 Fully Connected Layers

Fully connected layers are typically used towards the end of the network
for classification tasks. They flatten the feature maps and connect every
input neuron to every output neuron. Figure 2.2 illustrates a fully connected
layer’s input, weight, and output. This structure is a significantly dense
connection. The number of mathematical operations in a fully-connected
layer is much more than in a convolution layer, even though the input and
output tensors are much smaller than in a convolution layer. Due to their
dense connections, fully connected layers can be computationally intensive,
and various methods reduce their complexity, such as weight pruning [12].

2.1 convolutional neural networks

21

Collectively, the layers convolutional, activation, pooling, normalization,
and fully connected—form the backbone of CNN architectures. They work
in harmony to transform raw input data into meaningful representa-
tions through feature extraction in the earlier layers and ultimately refine
these representations into final predictions through classification (fully
connected) layers. Understanding the interplay and computational charac-
teristics of these layers is crucial for optimizing CNN performance, espe-
cially when deploying models on resource-constrained end devices. This
foundation sets the stage for exploring how CNNs are applied in practical
tasks, which are central to numerous real-world applications and directly
influence the efficiency considerations of AI.

2.1.3 CNN Applications and Architectures

CNNs have revolutionized various computer vision tasks, with object classi-
fication and object detection being two of the most prominent applications.
These tasks are pivotal to applications ranging from autonomous vehicles
and surveillance systems to content-based retrieval and medical imaging.
In this section, we examine these two tasks in detail, along with the
popular CNN architectures developed to address their specific challenges.
This examination not only highlights the computational demands of CNN
applications but also underscores the need for optimization in deploying
CNNs on end devices, where resource constraints are a critical factor.

2.1.3.1 Object Classification

Object classification involves assigning a label to an image from a prede-
fined set of categories. Common datasets used for benchmarking include
ImageNet [13], which contains millions of images across a thousand cat-
egories. The most widely used subset of ImageNet is the ILSVRC image
classification and localization dataset. This dataset spans 1000 object classes
and is divided into three subsets: 1,281,167 training images, 50,000 vali-
dation images, and 100,000 test images. The training dataset is used to
optimize the parameters of a model, enabling it to learn patterns from
labeled data. The validation dataset, which is labeled, is typically used for
hyperparameter tuning during training and to evaluate model performance
on unseen data. The test dataset, designed for competition purposes, is
unlabeled and requires predictions to be submitted for evaluation by the
organizers.The validation dataset is often used as a substitute for the test
dataset to measure the accuracy and performance of models.

22

background

Performance on ILSVRC is commonly measured using top-1 and top-
5 accuracy. Top-1 accuracy indicates the percentage of images for which
the model’s highest-confidence prediction matches the correct label. Top-5
accuracy considers the prediction to be correct if the correct label appears
among the model’s five most confident predictions. These metrics provide
insight into both the overall precision of a model and its ability to capture
multiple plausible labels in challenging cases.

In our research experiments, we utilized several well-known CNN archi-
tectures that are widely used for image classification tasks. These models
include AlexNet, GoogLeNet, MobileNet, ResNet50, and SqueezeNet. Each of
these architectures has unique design characteristics, such as the number
of layers, types of operations, and strategies for achieving efficiency and
accuracy. Below, we describe the structure, performance characteristics, and
specifications of each model used in our experiments.

• AlexNet [14]: Known for its pioneering architecture that won the
ImageNet challenge in 2012, AlexNet demonstrated the effectiveness of
deep CNNs in large-scale image classification. It consists of 8 layers:
5 convolutional layers for feature extraction and 3 fully connected
layers for classification. The network uses ReLU activation functions
to accelerate training and incorporates dropout to mitigate overfit-
ting. Max-pooling layers reduce spatial dimensions, and data aug-
mentation techniques like random cropping and mirroring enhance
generalization. AlexNet has approximately 60 million parameters and
achieved a top-1 accuracy of 63.3% and a top-5 accuracy of 84.6%
on the ILSVRC-2012 dataset. Its success popularized the use of HPC
GPUs for training deep CNNs.

• GoogLeNet [15]: Introduced in 2014, GoogLeNet significantly im-
proved computational efficiency by incorporating Inception modules.
These modules use parallel convolutional filters of different sizes
(1×1, 3×3, 5×5) to capture multi-scale features. To reduce the number
of parameters, it employs 1×1 convolutions (bottleneck layers) and
global average pooling instead of fully connected layers. The archi-
tecture comprises 22 layers and requires only 6.8 million parameters.
GoogLeNet achieved an impressive top-1 accuracy of 68.7% and a top-5
accuracy of 88.9% on the ILSVRC-2014 dataset.

• MobileNet [16]: Designed for mobile and embedded vision appli-
cations, MobileNet uses depthwise separable convolutions to reduce
the number of parameters and computational cost significantly. This

2.1 convolutional neural networks

23

approach replaces standard convolutions with a combination of
depthwise and pointwise convolutions. MobileNet supports adjustable
width and resolution multipliers, allowing trade-offs between accu-
racy and efficiency. With approximately 4.2 million parameters, it is
lightweight and ideal for resource-constrained applications. MobileNet
achieved a top-1 accuracy of 70.6% and a top-5 accuracy of 89.5% on
the ILSVRC-2012 dataset.

• ResNet50 [17]: ResNet50 is a 50-layer deep CNN that introduced
residual connections to improve training in deep networks. These
identity shortcut connections help mitigate performance degradation
as network depth increases, allowing stable optimization during train-
ing. The architecture includes 49 convolutional layers and one fully
connected layer. ResNet50 has approximately 25.6 million parameters
and achieved a top-1 accuracy of 76.0% and a top-5 accuracy of 93.0%
on the ILSVRC-2015 dataset, establishing a new benchmark.

• SqueezeNet [18]: SqueezeNet achieves AlexNet-level accuracy with 50
times fewer parameters (approximately 1.24 million). It employs five
modules, which consist of squeeze layers (1×1 convolutions) followed
by expand layers (a mix of 1×1 and 3×3 convolutions). Global average
pooling replaces fully connected layers, further reducing the parame-
ter count. SqueezeNet achieved a top-1 accuracy of 57.5% and a top-5
accuracy of 80.3% on the ILSVRC-2012 dataset [18]. It is known for its
small memory footprint, making it highly suitable for deployment on
devices with limited computational resources.

These models vary in depth, computational complexity, and performance,
providing a comprehensive basis for evaluating inference efficiency on end
devices. Research into lightweight models like MobileNet and SqueezeNet
highlights the importance of designing architectures suitable for resource-
constrained environments.

2.1.3.2 Object Detection

Object detection extends image classification by not only identifying object
categories but also localizing multiple objects within an image through
bounding boxes. A bounding box is a rectangular region that encloses an
object in an image, defined by its coordinates (x, y) for positioning and
width-height dimensions for scale. The ability to detect multiple objects
within an image makes object detection a more complex task than classifi-
cation, requiring simultaneous classification and localization. Additionally,

24

background

object detection models must handle challenges such as varying object
scales, overlapping objects, and the need for real-time performance, which
often demands high computational efficiency.

A widely used benchmark for object detection is the Common Objects in
Context or COCO dataset [19]. COCO 2017 includes 118,000 labeled images
for training and 5,000 labeled images for validation. In our experiments,
the validation dataset was used to evaluate the accuracy of object detection
models. COCO provides annotations for 80 object categories, covering
object segmentation, localization, and keypoint detection, making it one
of the most comprehensive datasets for object detection tasks.

A key metric for evaluating object detection models is mAP, which
quantifies both classification and localization accuracy. mAP is computed
as the mean of average precision scores across all object categories, where
average precision measures how well a model detects objects based on
precision-recall curves. A precision-recall curve plots precision, which is the
proportion of correct detections among all detections, against recall, which
represents the proportion of correctly detected objects among all ground-
truth objects, at different confidence thresholds. The average precision for
a given object category is calculated as the area under this curve.

To determine whether a detected bounding box is correct, object de-
tection models use IoU. IoU measures the overlap between a predicted
bounding box and the ground-truth bounding box, defined as:

IoU =

Area of Overlap
Area of Union

where the area of overlap is the intersection of the predicted and ground-
truth bounding boxes, and the area of union is the total area covered by
both boxes. A detection is considered correct if the IoU exceeds a predefined
threshold, typically set at 0.5. The mAP is then calculated using the IoU
threshold to assess detection accuracy across different object categories.
In our research, we focus on the YOLOv3 model for object detection:

• YOLOv3 [20]: YOLOv3 is a real-time object detection model designed
for high-speed processing while maintaining competitive detection
accuracy. Instead of performing separate localization and classifica-
tion steps, YOLOv3 predicts bounding boxes and class probabilities
in a single forward pass through the network, which improves in-
ference speed. The model incorporates multi-scale feature extraction
to detect objects of varying sizes and uses the Darknet-53 backbone,

2.2 on-device inference

25

a convolutional network with 53 layers and residual connections for
improved feature learning. YOLOv3 has approximately 62.9 million
parameters and achieves a mAP of 57.9% at an IoU threshold of
0.5, on COCO dataset. Its efficient single-pass architecture allows
fast inference, making it well-suited for real-time object detection on
resource-constrained devices.

As CNN applications expand to tasks like object classification and detec-
tion, deploying these models in real-world settings requires transitioning
from training to inference. While inference is computationally less demand-
ing than training, it remains a challenge—particularly for end devices
with limited processing power, memory, and energy availability. Many
detection models are optimized for high-performance computing environ-
ments, but executing them efficiently on resource-constrained hardware
requires specialized techniques. Optimizing inference for end deployment
is critical in applications such as autonomous systems, mobile devices, and
embedded vision, where real-time performance and efficiency are essential.
These challenges necessitate dedicated hardware and software strategies to
balance accuracy, latency, and energy efficiency.

2.2 on-device inference

Deploying CNNs on end devices requires specialized hardware and soft-
ware optimizations to meet computational demands within the constraints
of these platforms. Unlike traditional cloud-based processing, AI must
operate efficiently on hardware with limited power, memory, and com-
pute resources. These constraints necessitate tailored strategies to balance
performance, energy consumption, and latency while ensuring real-time
responsiveness. This section examines the hardware platforms and software
frameworks that enable efficient CNN inference on end devices, emphasiz-
ing the role of heterogeneous processing units in HMPSoCs.

2.2.1 Hardware Platform

HMPSoCs play a crucial role in optimizing CNN inference on end devices
by integrating multiple types of processing units to efficiently distribute
workloads. Unlike cloud-based architectures that rely on high-performance
GPUs and dedicated accelerators, end devices must balance speed, power
efficiency, and computational constraints within a single chip.

26

background

big CPU Cluster

A73 Core

A73 Core

A73 Core

A73 Core

A53 Core

A53 Core

Core

Core

LITTLE CPU Cluster

Mali-G52 MP4 GPU

L2 Cache

L2 Cache

L2 Cache

CCI Bus

DRAM

Figure 2.3: An abstract block diagram of Amlogic A311D HMPSoC in Khadas Vim 3

embedded platform.

A typical HMPSoC consists of multiple processing units, including CPUs,
GPUs, and NPUs, all interconnected through an on-chip communication
fabric. CPUs, often designed with big.LITTLE architectures, integrate high-
performance cores for compute-intensive tasks and power-efficient cores for
background workloads, enabling dynamic workload adaptation. Each CPU
cluster consists of multiple cores that share a low-latency interconnect, fa-
cilitating fast intra-cluster communication. However, communication across
CPU clusters or with other processing units relies on a cache-coherent
interconnect, introducing additional latency and energy overhead.

Figure 2.3 presents an abstract block diagram of an HMPSoC, specifically
the Amlogic A311D used in the Khadas VIM3 platform. This HMPSoC inte-
grates a hexa-core ARM big.LITTLE CPU, consisting of two CPU clusters:
a high-performance, high-power quad-core big CPU cluster and a low-
performance, low-power dual-core LITTLE CPU cluster. It also includes a
dual-core Mali G52 MP4 GPU, optimized for parallel computations.

Embedded GPUs within HMPSoCs are designed for parallel computa-
tion, making them well-suited for CNN inference workloads. Unlike server-
grade GPUs, which operate independently with dedicated high-bandwidth
memory, embedded GPUs share the main system memory (DRAM) with
CPUs. This shared memory access can create bandwidth contention when
both CPUs and GPUs require frequent access to the same memory re-
sources. The communication between CPUs and GPUs occurs over a shared
memory bus, introducing synchronization overhead when handling large
data transfers. Additionally, GPUs have different memory access patterns

2.2 on-device inference

27

compared to CPUs, which adds overhead to their communication and can
impact workload distribution efficiency.

Unlike server-grade GPUs, which operate independently with dedi-
cated high-bandwidth memory, embedded GPUs share the main mem-
ory (DRAM) with CPUs. This shared memory access can create bandwidth
contention when both CPUs and GPUs require frequent access to the
same memory resources. The communication between CPUs and GPUs
occurs over a shared memory bus, introducing synchronization overhead
when handling large data transfers. Additionally, GPUs have different
memory access patterns compared to CPUs, which adds overhead to their
communication and can impact workload distribution efficiency.

Efficient data access and communication among processing units rely
heavily on the hierarchical memory system, which consists of multiple
cache levels. Each CPU core has a private level-one (L1) cache, providing
fast access to frequently used data, but its limited capacity requires frequent
updates. To improve data sharing within clusters, CPUs utilize a level-
two (L2) cache, which is typically shared among multiple cores, reducing re-
dundant memory accesses to DRAM. Some HMPSoCs further incorporate a
level-three (L3) cache, shared across clusters, to improve data reuse across
different CPU cores. While caches reduce memory access latency, cache
coherence mechanisms must be carefully managed to ensure consistency
between processing units.

NPUs, introduced in more recent HMPSoCs, serve as dedicated accelera-
tors for DL workloads. These units are optimized for tensor computations
and often include specialized matrix multiplication circuits that enable
efficient execution of quantized networks. Unlike CPUs and GPUs, NPUs
typically function with dedicated internal memory buffers, reducing their
reliance on shared memory. This architectural choice allows NPUs to pro-
cess data with minimal memory contention, but careful coordination is still
required when exchanging data with other processors to avoid bottlenecks.
The integration of these diverse processing units within a single chip
enables lower-latency communication compared to cloud-based architec-
tures, where GPUs and accelerators are often off-chip and connected via
high-speed interfaces. On HMPSoCs, on-chip interconnects, such as ARM’s
AMBA CCI, allow for efficient data exchange. However, despite these advan-
tages, frequent data movement across different processing units remains a
critical factor in achieving high performance, requiring optimized workload
scheduling and synchronization techniques.

28

background

27

96

27

224

3

224

r
e
y
a
L

t
u
p
n
I

)
1
(

l

n
o
i
t
u
o
v
n
o
C

)
2
(

g
n

i
l

o
o
P
-
x
a
M

)
3
(

l

n
o
i
t
u
o
v
n
o
C

)
4
(

g
n

i
l

o
o
P
-
x
a
M

13

13

256

)
5
(

l

n
o
i
t
u
o
v
n
o
C

13 384
13

)
6
(

l

n
o
i
t
u
o
v
n
o
C

13 384
13

)
7
(

l

n
o
i
t
u
o
v
n
o
C

)
8
(

g
n

i
l

o
o
P
-
x
a
M

6 256
6

6
9
0
4

)
9
(

l

n
o
i
t
u
o
v
n
o
C

)
0
1
(

d
e
t
c
e
n
n
o
C
-
y
l
l

u
F

6
9
0
4

)
1
1
(

d
e
t
c
e
n
n
o
C
-
y
l
l

u
F

0
0
0
1

r
e
y
a
L

t
u
p
t
u
O

Figure 2.4: The CNN architecture for Alexnet.

e
d
o
N
t
u
p
n
I

W1

input

B1

1

e
d
o
N
n
a
M

i

W2

out1

B2

2

e
d
o
N
n
a
M

i

W3

out2

B3

3

e
d
o
N
n
a
M

i

W4

out3

B4

4

e
d
o
N
n
a
M

i

W5

out4

B5

5

e
d
o
N
n
a
M

i

W6

out5

B6

6

e
d
o
N
n
a
M

i

W7

out6

B7

7

e
d
o
N
n
a
M

i

W8

out7

B8

8

e
d
o
N
n
a
M

i

out8

e
d
o
N
t
u
p
t
u
O

Figure 2.5: Alexnet graph in ARM-CL corresponding to its CNN architecture.

Figure 2.3 illustrates the interconnection between CPU, GPU, and mem-
ory within an HMPSoC, highlighting key components that influence CNN
inference performance. The ability to distribute CNN workloads efficiently
across these heterogeneous processors is essential for achieving optimal
latency and power efficiency. Examples of HMPSoCs used in our research
include the Amlogic A311D (integrated into the Khadas VIM3 platform),
which features a hexa-core ARM big.LITTLE CPU and a dual-core Mali
G52 MP4 GPU, and the RK3399Pro (used in the Rock Pi N10 platform),
which incorporates a hexa-core ARM big.LITTLE CPU, a quad-core Mali
T860 GPU, and a dedicated NPU. These architectures illustrate the diversity
of processing units available in modern end devices and highlight the need
for optimized inference strategies that leverage each component effectively.
Efficiently running CNNs on HMPSoCs requires careful consideration of
their architectural characteristics, communication mechanisms, and mem-
ory hierarchy. Optimized resource allocation strategies must account for
data locality, memory access patterns, and inter-processor communication
to minimize bottlenecks and maximize throughput. When designing solu-
tions for HMPSoCs, it is essential to align optimizations with hardware
structure to effectively utilize heterogeneous and resource-constrained pro-
cessing units, ensuring both performance and energy efficiency.

2.2 on-device inference

29

2.2.2 Software Framework

Optimized software frameworks play a crucial role in enabling efficient
CNN inference on HMPSoCs by tailoring execution to the architectural
characteristics of their processing units. These frameworks are specifically
designed to optimize inference within a single processor—either a CPU
or a GPU—by efficiently parallelizing computations across its cores. They
provide structured APIs for defining CNN models and translating them
into computation graphs that are executed using processor-specific op-
timizations, including memory management, workload scheduling, and
kernel execution. However, these frameworks do not inherently distribute
computations across multiple processors, highlighting the need for further
solutions to leverage the full potential of heterogeneous architectures.

ARM-CL is a widely used framework optimized for DL inference on ARM
Cortex-A CPUs and Mali GPUs. It provides a collection of low-level machine
learning functions that accelerate computations using NEON instructions
on CPUs and OpenCL on GPUs. ARM-CL enables users to define CNN
architectures using a structured API, as illustrated in Figure 2.4, which
presents the abstract block diagram of AlexNet, showing its layers and
interconnections (tensors). Given such a user-defined architecture, ARM-CL
constructs an equivalent computation graph representation for execution
on the underlying hardware.

Figure 2.5 depicts the corresponding ARM-CL computation graph for
AlexNet, where CNN layers are transformed into a graph-based model
with nodes representing computational operations and edges defining data
dependencies. In this graph, CNN layers are represented as interconnected
nodes, following a sequential consumer-producer relationship. The Input
and Output nodes define the CNN’s input and output layers, respectively,
while Main nodes represent key computational layers such as convolution,
normalization, and fully connected transformations. Each Main node is
associated with a Weight and a Bias node, which store the corresponding
parameters. Notably, the number of Main nodes does not necessarily match
the number of layers in the CNN, as certain operations may be fused
for efficiency, and auxiliary layers such as normalization and activation,
if separate, are not considered Main nodes.

ARM-CL begins execution by loading the CNN input into the Input node,
initiating data propagation through the network. Each layer processes its
input data until the final Output node produces the result. The framework
optimizes execution based on the selected processor. On CPUs, it partitions

30

background

matrix operations across multiple worker threads, optimizing data place-
ment to reduce cache misses. On GPUs, workloads are scheduled through
the OpenCL queue, enabling efficient parallel execution across GPU cores.
To further improve efficiency, ARM-CL divides CNN computations into
optimally sized chunks based on cache hierarchy and execution capabilities.
Dynamic scheduling within cores of a single processor ensures minimal
idle time and has low communication overhead, optimizing memory access
patterns and overall inference performance.

Convolutional layers, which dominate CNN architectures, perform ma-
trix operations using specialized kernels. The efficiency of these operations
depends on input size, weight matrices, and memory access patterns.
ARM-CL provides optimized kernel implementations for each processor,
ensuring that layer operations execute with minimal overhead. Backend
execution contexts are tailored to the selected processor: on CPUs, tasks
are distributed across cores while considering cache sizes, and on GPUs,
an OpenCL execution context is configured for efficient parallel execution.
ARM-CL also applies processor-specific optimizations, such as NEON in-
structions for CPUs and OpenCL-based techniques for GPUs.

Despite these optimizations, ARM-CL only supports single-processor
execution, which becomes a bottleneck when higher throughput and lower
latency are required for real-time applications. Unlike in cloud-based
systems, where GPUs significantly outperform CPUs, the computational
power of embedded CPUs and GPUs in HMPSoCs is often comparable.
This makes multi-processor execution crucial for improving CNN inference
performance. However, distributing workloads across multiple processors
introduces challenges such as context-switching overhead, memory syn-
chronization issues, and inter-processor communication delays.

The lack of multi-processor support in ARM-CL highlights the need for
additional techniques to efficiently utilize all available processing units.
While ARM-CL optimizes execution within individual processors, achiev-
ing efficient inference across multiple heterogeneous processors requires
further strategies to balance execution across CPUs, GPUs, and NPUs while
minimizing communication overhead.

2.3

efficiency aspects of on-device inference

Optimizing CNN inference on resource-constrained end devices demands
a careful balance of multiple efficiency aspects, including performance,
power consumption, and accuracy. Efficient on-device inference is charac-

2.3 efficiency aspects of on-device inference

31

terized by achieving low latency and high throughput while minimizing
power consumption and maintaining accuracy within acceptable limits.
Given the constraints of end devices and the comparable computing power
of the processors, the adaptive utilization of available hardware resources
in HMPSoCs is necessary to meet these objectives.

In this section, we explore the key efficiency considerations for on-device
inference, addressing performance aspects like latency and throughput,
power efficiency and consumption, and accuracy trade-offs. These consid-
erations are foundational to enhancing CNN inference on end devices,
balancing the requirements of real-time processing, energy conservation,
and application accuracy.

2.3.1 Performance-Efficient Inference

Performance optimization focuses on achieving low-latency and high-
throughput CNN inference, which is critical for real-time applications.
While optimizing computation within a single processor is crucial, achiev-
ing efficient DNN inference on end devices often requires leveraging both
CPU and GPU processors. Unlike powerful servers, where GPUs signif-
icantly outperform CPUs for DNN inference, the performance of GPUs
and CPUs in end devices is often comparable. However, evaluations reveal
that parallelizing the execution of a single layer across cores of different
processors is inefficient. The high cost of inter-processor communication
degrades performance due to substantial synchronization and data transfer
overhead. This underscores the need for strategies that effectively integrate
CPU and GPU processors while minimizing inter-processor communication
to optimize DNN inference performance.

2.3.1.1 Latency Optimization

Latency refers to the time required to process a single input through a DNN,
encompassing the loading and preparation of the input image with the
initial layer, the processing and transfer through hidden layers, and finally,
the post-processing in the output layer to extract the result. Minimizing
latency is critical for applications demanding immediate responses, such as
autonomous driving and robotics.

In ARM-CL, the workload of each function (or task) is distributed among
the cores of a single processor (GPU or CPU cluster). However, parallelizing
the workload of a layer across multiple processors is often inefficient. The
straightforward approach for minimizing inference latency, when relying

32

background

on off-the-shelf frameworks, is identifying the fastest processor for the
given DL model. Running inference on the cores of this processor generally
yields the lowest latency.

As shown in Figure 1.2 of Chapter 1, embedded GPUs often have
comparable performance to CPU clusters, and in some cases, CPUs may
even outperform GPUs. Consequently, selecting the most suitable processor
for running a model is crucial for achieving optimal latency. However, DL
models are not monolithic tasks but are composed of multiple layers, each
with distinct characteristics. To further improve latency, different layers
or parts of a model can be executed on the most efficient processor for
their specific computational needs. In Chapter 3, we analyze inference
latency by exploring the performance efficiency of different layer types,
sizing parameters, and their execution on various processors. In addition
to processor performance, inter-processor communication between layers
must also be considered, as it can contribute significantly to overall latency.
Achieving optimal latency in heterogeneous environments presents sev-
eral challenges. Processor heterogeneity, where CPUs and GPUs differ
in architecture and execution models, makes seamless switching between
processors complex. Managing the overhead introduced by switching pro-
cessors is critical, as poorly managed overheads can negate latency gains.
Moreover, existing frameworks often lack native support for mid-inference
processor switching, necessitating custom implementations to bridge this
gap. These challenges must be addressed to enable efficient inference across
diverse processor architectures.

2.3.1.2 Throughput Optimization

Throughput refers to the number of inputs processed per unit time, often
measured in FPS. High throughput is essential for processing data streams
or batch inputs, particularly in real-time applications. When throughput
falls below the input rate of frames to be processed, buffering occurs,
which increases inference latency. Improving throughput requires efficient
utilization of processing resources. A straightforward approach is to use all
processors independently, each handling different frames. While this can
increase throughput, it introduces several challenges.

Firstly, running processors independently results in uneven latency, with
the slowest processor determining the overall latency, commonly referred to
as worst-case latency. Secondly, each processor must load the entire model
into memory, which is problematic given the limited memory capacity of
resource-constrained devices—especially as DL models continue to grow in

2.3 efficiency aspects of on-device inference

33

size. Additionally, as mentioned earlier, parallelizing a single layer across
multiple processors is inefficient due to the high communication demands
and significant inter-processor communication overhead.

Pipelining inference execution across multiple processors offers a solu-
tion that avoids the synchronization and communication challenges within
individual layers. In this approach, the CNN is divided into subgraphs,
which are then mapped to stages, with each stage assigned to a specific
processor. Each processor handles all layers within its assigned subgraph,
ensuring that the synchronization and communication overheads remain
confined within a single processor. This intra-processor design minimizes
the need for costly inter-processor communication, which is limited to the
boundary layers of the subgraphs. Data is transferred between processors
only at these boundaries, reducing overhead while enabling different parts
to process consecutive frames in parallel.

This pipelined execution allows multiple inputs to be processed simul-
taneously in different stages, significantly improving throughput without
greatly increasing latency. By leveraging intra-core parallelization within a
processor for each layer and inter-processor parallelization for subgraphs,
throughput is maximized. Additionally, by grouping consecutive layers
into subgraphs, inter-subgraph communication is minimized. This design
ensures that each processor loads only a portion of the model into memory,
balancing memory usage and reducing overhead. The result is balanced
and consistent latency across frames.

Achieving optimal throughput using pipelining presents several chal-
lenges. Load balancing is critical to ensure that no pipeline stage be-
comes a bottleneck, requiring each stage to handle a comparable workload
for maximum efficiency. Additionally, managing synchronization between
processors is essential, as data dependencies between subgraphs require
careful coordination to avoid delays or bottlenecks. Memory synchroniza-
tion between pipeline stages—or, more generally, efficient data transfer
among processors—is also a key challenge, as improper handling can lead
to latency overhead. These considerations are fundamental to designing
efficient pipelined systems for real-time applications.

2.3.2 Power-Efficient Inference

Power consumption and power efficiency are critical considerations for
optimizing inference on end devices, particularly given their thermal and
energy constraints. Power consumption refers to the amount of electrical

34

background

power drawn by a processor or system during operation, typically mea-
sured in watts. Higher power consumption generates more heat, which
can lead to thermal instability and performance throttling if not managed
properly. Unlike server-grade hardware, which benefits from active cooling
solutions such as fans and heat sinks, most end devices lack dedicated cool-
ing systems and must instead rely on passive heat dissipation. Additionally,
these devices operate under strict power budgets, meaning they must limit
power draw to avoid exceeding design constraints.

Power efficiency focuses on how effectively a system utilizes power to
perform computations. In battery-powered devices, improving power effi-
ciency directly extends battery life by ensuring that more inferences can be
executed per unit of energy. In the context of DL inference, power efficiency
is often evaluated in terms of inferences per watt, where a model that
performs more inferences while consuming less power is considered more
efficient. While reducing power consumption helps manage thermal and
power constraints, increasing power efficiency ensures that performance is
maintained while minimizing energy usage.

A common strategy for improving power efficiency in processors is DVFS,
which dynamically adjusts the voltage and operating frequency based on
workload demands. By lowering the frequency during less computationally
intensive tasks, DVFS reduces power consumption and helps maintain
thermal stability. However, despite its benefits, it introduces trade-offs
that must be carefully managed. Reducing the frequency leads to longer
execution times, which can increase overall latency and negatively impact
real-time applications. The impact of DVFS on performance varies across
different processor architectures, requiring careful tuning to balance power
savings and execution speed.

Applying DVFS in DL inference presents additional challenges. Fine-
grained adjustments at the layer level require precise scheduling to avoid
inefficiencies, as rapid frequency changes can introduce overhead. Further-
more, not all layers of a neural network have the same computational
demands, meaning that a one-size-fits-all DVFS strategy may not be ef-
fective. Hardware constraints, including processor transition delays and
voltage scaling limits, necessitate adaptive approaches that optimize power
efficiency without significantly degrading inference speed.

Balancing power efficiency and latency is critical in end devices, as
reducing power consumption should not come at the cost of increased
inference time. Achieving this requires a combination of techniques, such
as layer-wise DVFS, intelligent layer mapping, and dynamic processor

2.3 efficiency aspects of on-device inference

35

selection. These approaches help ensure that power-saving strategies do
not introduce excessive delays, allowing real-time applications to maintain
responsiveness while operating within thermal and energy constraints.

2.3.3 Accuracy Trade-offs

Maintaining model accuracy is essential in DL inference. However, achiev-
ing high performance and power efficiency often requires trade-offs in
computational complexity, memory usage, or precision. This is particularly
important for resource-constrained end devices, where limited computa-
tional resources, power budgets, and memory availability necessitate opti-
mizations that may impact accuracy. Balancing these factors is critical to
ensure practical usability without compromising application requirements.
Quantization is a technique used to reduce the precision of a model’s
parameters (weights) and activations—the intermediate outputs computed
by each layer during inference. Depending on the quantization method,
either just the model parameters or both parameters and activations may
be quantized. For instance, instead of representing these values in 32-bit
floating-point precision, quantization converts them into lower-precision
formats, such as 8-bit integers. This reduction minimizes memory usage,
computational complexity, and power consumption, making quantization
particularly advantageous for resource-constrained devices.

In quantized inference, operations within each layer, such as matrix
multiplications and convolutions, are performed using quantized values.
After a layer processes its inputs, the output (activation) may be quantized
again before being passed as input to the next layer. This ensures efficient
processing throughout the network while managing precision loss.

Quantization benefits embedded devices in several ways. By reducing
data size, it decreases memory requirements, which is critical for devices
with limited capacity. It also simplifies arithmetic operations, allowing for
faster computations. Modern end devices increasingly feature specialized
NPUs, designed to handle quantized data efficiently. NPUs leverage hard-
ware optimizations like dedicated MAC units for low-precision integers,
achieving superior performance and power efficiency compared to general-
purpose processors. This synergy between quantized models and NPUs is
a key enabler for real-time, power-efficient inference on end devices.

Despite its advantages, quantization can lead to accuracy loss due to
the approximation of values. Some models, particularly those sensitive to
small numerical changes, may experience a significant drop in accuracy

36

background

when quantized. For example, YOLOv3 shows a noticeable decline in
performance when fully quantized, highlighting model-specific trade-offs.
Quantization is typically applied using PTQ or QAT methods. PTQ
involves quantizing a pre-trained model without retraining. It uses a small
set of unlabeled data to analyze the distribution of activations and compute
quantization factors (scaling parameters) for weights and/or activations.
PTQ is computationally efficient and does not require a labeled dataset,
making it ideal for inference-focused workflows like ours. However, it may
introduce higher accuracy loss in comparison to more sophisticated meth-
ods. QAT integrates quantization into the training process by simulating the
effects of quantized weights and activations during training or retraining.
This allows the model to adapt to precision changes, resulting in better
accuracy retention compared to PTQ. However, QAT requires additional
computational resources and access to labeled datasets. In our work, we
focus on PTQ due to its simplicity, independence from labeled datasets,
and compatibility with end device constraints, where inference rather than
training is the primary concern.

2.4 challenges

Efficient on-device inference involves overcoming several technical and
design challenges. These challenges span processor integration, model
preparation, profiling, and optimization in complex design spaces.

2.4.1 Technical Challenges

Efficient inference on heterogeneous processors such as CPUs, GPUs, and
NPUs requires addressing multiple technical hurdles:

Integration of Heterogeneous Processors: Combining different proces-
sors in a unified inference framework demands careful management of exe-
cution contexts, data movement, and synchronization. Each processor type
has distinct execution environments and programming models—CPUs may
use NEON instructions, GPUs operate with OpenCL, and NPUs often rely
on proprietary interfaces. Efficiently transferring data between processors
is crucial to prevent bottlenecks, and synchronization ensures consistent
data handling and correct execution order.

Model Format Compatibility: Pretrained models are typically developed
using Python-based libraries, whereas efficient frameworks for running
inference on CPUs and GPUs of end devices (e.g., ARM-CL) are imple-

2.4 challenges

37

mented in C++. This format and interface disparity necessitates converting
pretrained models into formats compatible with these frameworks and ex-
tracting layer parameters for use in C++. Meanwhile, NPUs rely on vendor-
specific tools and libraries to convert models into proprietary formats,
which are entirely different from CPU and GPU contexts. Integrating these
formats into a unified framework is challenging, requiring careful synchro-
nization and handling of models across different formats. Moreover, each
NPU requires its own specific methods, libraries, and tools for preparing
and running models, adding another layer of complexity.

Closed-Source NPUs: Many NPUs are vendor-specific, with proprietary
software stacks that limit access to low-level operations. This creates signifi-
cant integration challenges, as developers must devise creative solutions to
interface with NPUs without direct access to their internal functionalities.
Profiling and Power Measurement: Accurate profiling of timing and
power consumption is critical for optimization but presents challenges due
to missing power sensors and the small time scales of some operations. To
address this, a custom power measurement system was implemented using
an INA260 power sensor. This system measures the power consumption of
the entire SoC with a sampling interval of approximately 3 ms, enabling
precise measurements needed for optimization efforts.

2.4.2 Design and Optimization Challenges

Optimizing inference efficiency requires navigating an enormous design
space. This space is defined by a multitude of parameters—from processor
mappings to voltage-frequency scaling and quantization settings—each
affecting performance, energy consumption, and accuracy.

Huge Design Space: The sheer number of possible configurations poses
a significant challenge. The design space grows exponentially with the
number of layers, available processors, and optimization parameters. Even
minor adjustments to layer assignments or system settings can lead to
substantial variations in outcomes. Given the impracticality of brute-force
exploration, heuristic and probabilistic methods are necessary to guide
the search toward promising configurations. Additionally, hardware con-
straints make exhaustive evaluation infeasible, necessitating the use of
efficient search algorithms for efficient exploration.

Multi-Objective Optimization and Trade-Offs: Optimizing DL inference
requires balancing multiple, often conflicting, performance metrics, such as
latency, throughput, power consumption, and accuracy. Reducing power

38

background

consumption may come at the cost of lower throughput while improving
accuracy can increase computational demands. The complexity is further
amplified by real-world constraints—some applications may enforce strict
latency limits while aiming to minimize energy consumption.

Time-Consuming Design Evaluation and Estimation Models: Even
with efficient search algorithms, exploring a sufficient number of design
points is necessary to find near-optimal solutions. However, evaluating each
candidate configuration remains computationally expensive, often requir-
ing detailed profiling that takes several minutes or longer. This evaluation
overhead makes rapid exploration challenging, necessitating the use of
estimation models to approximate performance, power consumption, and
accuracy without performing full evaluations.

These models must capture key interactions, including processor behav-
ior, layer dependencies, and system-level effects such as processor switch-
ing and data transfer overheads. However, constructing reliable estimation
models presents challenges, particularly in acquiring sufficient data to
ensure accurate predictions. Since profiling all configurations is infeasible,
efficient data-driven approaches are required to balance accuracy and
computational cost, enabling faster yet effective design space exploration.

2.5

summary

In this chapter, we explored the foundational concepts essential to under-
standing the challenges of deploying CNNs on resource-constrained end
devices. We provided an overview of CNN architectures, highlighting their
structure, layer types, and computational characteristics. This foundation
sets the stage for discussing the hardware and software frameworks critical
for enabling efficient on-device inference, with a focus on HMPSoCs. Key
efficiency considerations—such as latency, throughput, power consump-
tion, and accuracy—were examined, emphasizing the need for tailored
optimization strategies to address the unique constraints of end devices.

Beyond these foundational concepts, we identified critical challenges
in achieving efficient and accurate inference on heterogeneous platforms.
These include addressing model format incompatibilities, overcoming inte-
gration barriers for proprietary NPUs, and managing the vast design space
of optimization configurations. These discussions underline the significance
of bridging theoretical advancements in DL inference with practical deploy-
ment strategies, setting the stage for the novel methods and frameworks
presented in subsequent chapters.

3

L AY E R - S W I T C H E D L O W L AT E N C Y
I N F E R E N C E

Building on the foundational discussions in Chapters 1 and 2, this chapter
focuses on a key challenge in deploying CNNs on end devices: reducing
inference latency on HMPSoCs. Modern HMPSoCs combine embedded
CPUs and GPUs, each with distinct performance characteristics. Our central
insight is that individual layers within a CNN can achieve lower latency
when executed on the processor best suited to its computational profile.

In this chapter, we present a detailed analysis of the performance differ-
ences between CPU and GPU execution for various CNN layers. We then
introduce our novel, dynamic layer-level switching strategy that selects
the most efficient processing unit for each layer—even when incurring
the overhead of switching between different ISAs and execution models.
The insights and methodologies developed in this chapter contribute to
addressing RQ1, which investigates effective strategies for minimizing
inference latency on HMPSoCs. Our experiments on the Khadas VIM 3
board with an Amlogic A311D HMPSoC demonstrate an average latency
reduction of 4.72%, underscoring the promise of this approach.

This chapter is based on:

• E. Aghapour, D. Sapra, A. Pimentel, A. Pathania "CPU-GPU Layer-Switched
Low Latency CNN Inference" [21], in 25th Euromicro Conference on Digital
System Design (DSD), 2022

39

40

layer-switched low latency inference

3.1

introduction

Pattern recognition problems originate in many embedded applications in
various domains, such as autonomous driving [22], intelligent robotics [23],
image classification [16], object detection [24], and semantic segmenta-
tion [25]. It is now commonplace to solve (inference) these problems using
CNNs, known for their high accuracy in differentiating between patterns.
The time-sensitive nature of these applications requires CNN inference to
occur on end devices that run the embedded applications themselves [26].
HMPSoCs powering the end devices make on-device inference possible.
However, CNN kernels within the embedded applications project signif-
icant resource requirements on the underlying HMPSoCs. Consequently,
HMPSoCs often struggle to provide low latency embedded CNN inference
needed for high-end embedded applications.

An HMPSoC tightly integrates an embedded CPU and a GPU on a single
chip. An overview of the Amlogic A311D HMPSoC used in this work is
provided in Figure 2.3 in Chapter 2. This SoC consists of a hexa-core ARM
big.LITTLE CPU, which includes a quad-core big CPU cluster (with four
high-performance cores) and a dual-core LITTLE CPU cluster (with two
low-power cores). Additionally, it features a dual-core Mali GPU, both of
which can perform CNN inference [27].

It is common in non-embedded platforms for GPUs to significantly
outperform CPUs in inference. However, in embedded platforms, CPU
and GPU performance is often comparable, and in some cases, the CPU
can even outperform the GPU for certain CNNs. Consequently, CPUs
remain relevant for inference in embedded platforms [28]. Figure 1.1 in
Chapter 1 illustrates the latency of different CNNs on various HMPSoC
components (CPU or GPU). The big CPU always provides lower latency
than the LITTLE CPU. It is not feasible to use the big and LITTLE CPUs
simultaneously to reduce latency [29]. Therefore, we limit ourselves to only
the big CPU in this work. When referring to the CPU in this study, it specifi-
cally denotes the big CPU. Figure 1.1 also shows that the CPU outperforms
the GPU for MobileNet and ResNet50, while the GPU outperforms the CPU
for AlexNet, GoogleNet, and SqueezeNet.

It is common to run CNN kernels in an embedded application on
the HMPSoC component (CPU or GPU) that provides the lowest latency.
However, a CNN is not one monolithic execution block. A CNN comprises
several layers that execute sequentially to generate an output from a given
input. In this chapter, we observe that some of these layers execute faster

3.1 introduction

41

Table 3.1: Processing time of AlexNet layers on CPU and GPU. The last column

shows the time with the best component.

Layer

CPU (ms) GPU (ms)

Best (ms)

1

2

3

4

5

6

7

8

Total

11.56

15.05

5.15

4.48

3.41

38.51

17.02

4.19

99.38

9.69

14.37

8.62

5.33

4.15

35.89

10.06

3.44

91.55

9.69

14.37

5.15

4.48

3.41

35.89

10.06

3.44

86.50

on the CPU while the other layers execute faster on the GPU. Reducing the
latency for a CNN inference appears straightforward by executing a given
CNN layer on the HMPSoC component, where it performs the fastest. CPUs
and GPUs, however, have different ISAs and execution models. Therefore,
achieving a CPU-GPU layer-switched execution in practice is technically
challenging on a real platform.

Motivational Example: AlexNet is a popular CNN used for image classifi-
cation. The AlexNet contains 11 layers – five convolution, three max-pooling,
and three fully connected layers. Max-pooling layers are too small for us to
measure and work with individually. Therefore, we club them with the
preceding convolution layers to reduce the number of operatable layers
in AlexNet to eight. Table 3.1 shows the split of AlexNet latency on the
CPU and the GPU in terms of its layers. Layers 1, 2, 6, 7, and 8 execute
faster on GPU. Layers 3, 4, and 5 execute faster on the CPU. Table 3.1
also shows the hypothetical latency of AlexNet, assuming we execute each
layer on the fastest HMPSoC component (CPU or GPU). Latency of AlexNet
in such a hypothetical CPU-GPU layer-switched execution is 12.96% and
5.51% lower than CPU- and GPU-only execution, respectively. In practice,
a CPU-GPU layer-switched execution will also inherently have additional
latency overheads of switching between CPU and GPU and vice versa.

42

layer-switched low latency inference

Our Novel Contributions: We make the following novel contributions

within the scope of this work.

• Based on their properties, we provide reasoning for a layer executing

faster on the CPU than GPU and vice versa.

• We show a CPU-GPU layer-switched execution can reduce the latency
of CNN in practice on a real-world embedded platform, even with the
overheads involved.

Open Source Contribution: The code for the CPU-GPU layer-switched
execution is publicly available for download at https://github.com/Ehsan-
aghapour/ARMCL-pipe-all ("n-pipe-1" branch) under MIT license.

3.2 related work

In research, there are several optimizations, such as model architecture
search [30], quantization [31], weight compression [32], and graph prun-
ing [33], to execute CNNs entirely at the end devices. On the other hand,
there is research to run CNNs on resource constraint end devices in their
original form. Authors of [34] and [35, 36] propose an efficient hardware
design for CNN inference on FPGAs and CGRAs, respectively. However,
most end devices in practice utilize CPUs and GPUS within of-the-shelf
HMPSoCs for CNN inference [27].

Most current ML frameworks on devices use embedded CPUs rather than
GPUs [29], mainly because previously embedded GPU performance was in-
sufficient in end devices [28]. However, embedded GPUs have significantly
improved performance since then, but they are still nowhere near their
non-embedded counterparts. Therefore, several efforts have been made to
synergistically employ both CPUs and GPUs within HMPSoCs for high-
performance inference with CNNs [28, 37–42]. The authors of [29] were the
first to create a high-throughput pipeline between the CPU clusters of an
asymmetric multi-core for CNN inference. Authors of [43] propose a high-
throughput CNN inference pipeline between the CPU and GPU. However,
a pipeline design can only improve inference throughput, not latency.

MOSAIC [38] and DeepX [41] propose CNN model partitioning tech-
niques that map the sliced model shards onto multiple HMPSoC compo-
nents. DeepMon [39] partially offloads computation for convolution opera-
tions to GPU and thereby utilizes both CPU and GPU to minimize the infer-
ence latency. µLayer [40] intelligently maps ML inference tasks to CPU and
GPU on end devices, leveraging layer distribution and processor-specific

3.3 experimental setup

43

GPU

2

e
d
o
N
n
a
M

i

e
d
o
N
t
u
p
n
I

1

e
d
o
N
n
a
M

i

big CPU

3

e
d
o
N
n
a
M

i

out3

e
d
o
N

r
e
f
s
n
a
r
T

Sync

Trans

e
d
o
N

r
e
v
i
e
c
e
R

out3

4

e
d
o
N
n
a
M

i

5

e
d
o
N
n
a
M

i

out5

e
d
o
N

r
e
f
s
n
a
r
T

Sync

Trans

e
d
o
N

r
e
v
i
e
c
e
R

out5

6

e
d
o
N
n
a
M

i

GPU

7

e
d
o
N
n
a
M

i

8

e
d
o
N
n
a
M

i

t
u
p
t
u
O

Figure 3.1: The three sub-graphs for Alexnet obtained from partitioning it into three

sub-networks, mapped on GPU, big CPU and GPU, respectively.

quantization techniques. The authors of [44] propose a CNN inference
latency prediction model for GPU and design multipath neural networks,
enabling the runtime to choose a path that meets latency constraints.
However, none of the above works propose a CPU-GPU layer-switched
execution to reduce the latency of CNN inference.

3.3

experimental setup

We use Khadas Vim 3 embedded platform in this work. An Amlogic A311D
HMPSoC, as shown in Figure 2.3 in Chapter 2, powers the Khadas Vim
3 platform. The platform has a hexa-core asymmetric ARM big.LITTLE
multi-core CPU with two CPU clusters, big and LITLLE. This work uses
only the big CPU in this work. The quad-core big CPU contains four
A73 cores. The HMPSoC contains a dual-core Mali G52 MP4 GPU. The
operational (maximum available) frequency for the big CPU and GPU are
2.2 GHz and 0.8 GHz, respectively. A 4 GB LPDDR4 is the main memory for
the HMPSoC. The platform is running Android v9.0 with kernel v4.9. On
top of that, we use ARM-CL v21.02 in this work for CNN inference.

We use multiple CNN models, namely AlexNet, GoogleNet, MobileNet,
ResNet50, and Squeezenet, as the application kernels. These CNNs perform
image classification on the ImageNet for 1000 image classes. The input to
these models is an image of size (224 × 224) with three channels (RGB),
and the output is a tensor of size 1000 that predicts the input image class.

3.4 cpu-gpu layer-switched inference with arm-cl

ARM-CL provides an efficient execution framework for CNN inference
on ARM-based HMPSoCs. It optimizes layer execution for either CPUs
or GPUs but lacks support for dynamically switching layers between
processors during inference. Since the performance of embedded CPUs and

44

layer-switched low latency inference

GPUs is often comparable, selectively assigning layers to the processor that
executes them most efficiently can reduce CNN inference latency.

This section describes the modifications made to ARM-CL to enable
CPU-GPU layer-switched execution. ARM-CL represents CNNs as directed
computation graphs, where each layer is assigned to a single processor. By
default, ARM-CL executes the entire CNN on the selected processor (either
CPU or GPU). To enable CPU-GPU switching, we introduce a partitioning
approach that divides the computation graph into subgraphs, where each
subgraph consists of consecutive layers that execute on the same processor.
Layers can now be grouped into CPU or GPU subgraphs based on their
computational characteristics.

To facilitate execution across processors, two new graph nodes, Transfer
and Receiver, are introduced. A Transfer node marks the point where
execution switches from one processor to another. It stores the output
tensor from the preceding subgraph and initiates data movement to the
target processor. The corresponding Receiver node waits for this data
before resuming execution. These nodes ensure synchronized execution
and minimize unnecessary memory transfers.

Figure 3.1 illustrates an example of a partitioned CNN computation
graph for AlexNet, where execution begins on the GPU, switches to the CPU
for selected layers, and then switches back to the GPU for the remaining
layers. The Transfer and Receiver nodes enable seamless execution across
heterogeneous processors. During execution, ARM-CL loads the CNN input
into the Input node and propagates data through the computation graph.
The framework detects the first processor in the sequence and initializes
execution accordingly. When a Transfer node is encountered, execution
pauses, and the intermediate output is transferred to the memory space of
the target processor. The Receiver node on the target processor waits for
this transfer to complete before resuming execution. The process continues
until the final result is produced by the Output node.

Since CPU and GPU subgraphs share system memory in most HMPSoCs,
direct memory access techniques are leveraged to minimize transfer over-
head. Synchronization between CPU and GPU subgraphs is handled using
wait queues, ensuring that execution resumes as soon as the required data
is available. Memory buffers are managed efficiently to reduce redundant
data transfers, further optimizing execution.

Partitioning a CNN for CPU-GPU execution requires careful considera-
tion of layer complexity, memory bandwidth requirements, and processor-
specific optimizations. Profiling tools are used to analyze individual layer

3.5 layer latency analysis

45

performance and guide partitioning decisions, ensuring that each layer runs
on the most efficient processor to minimize overall inference latency while
maintaining an optimal workload distribution. Since the execution time of
a layer depends on its computational characteristics and memory access
patterns, the next section examines the impact of layer-specific parameters,
particularly their size and dimensions, to determine why certain layers
execute faster on the CPU while others perform better on the GPU.

3.5

layer latency analysis

A CNN is a sequence of layers that process a given input consecutively to
generate an output. Each layer of the neural network processes the input
from the preceding layer in the form of a tensor. Layers have associated
trainable parameters (weights and biases) that remain unchanged during
the inference and load at the set-up time to process this data. The output
of the layers is a tensor, computed by the multiplication operation between
its input and weight tensors, followed by an addition operation with the
bias matrix. Each layer loads its input data into the memory of the target
processor (CPU or GPU) and produces the output tensor for the next layer.
We have provided a detailed explanation of the different types of CNN
layers in Section 2.1.2.1 of the Chapter 2, including their structure and
operations. Building upon that discussion, we now analyze the impact
of layer-specific parameters, particularly their size and dimensions, on
execution time on CPU and GPU. We further investigate why certain layers
execute faster on the CPU while others perform better on the GPU, based
on the size of their parameters.

3.5.1 Effect of Parameters Size on Latency

We observe that some layers within a CNN execute faster on the CPU while
other layers perform better on the GPU. We aim to find the reason behind
the best HMPSoC component (CPU or GPU) for layers considering their
operation types and the size of their parameters. For this purpose, we
compare the CPU and GPU layer processing time with different parameter
sizes. First, we measure the layer processing time with the CPU (TCPU) and
the GPU (TGPU). Then, we use the measurements to calculate the ratio of
TCPU to TGPU (TCPU/GPU). When the value of this ratio is less than one,
the CPU is faster than GPU in processing the layer. When it is bigger than
one, GPU is faster than the CPU.

46

layer-switched low latency inference

Convolution

Normalization

Pooling

Total

7 14 28 56

112

224

Input Shape

(a) Filters = 32

U
P
G
/
U
P
C
T

U
P
G
/
U
P
C
T

2

1

0

4

2

0

U
P
G
/
U
P
C
T

U
P
G
/
U
P
C
T

3

2

1

0

4

2

0

7 14 28 56

112

224

Input Shape

(b) Filters = 64

7 14 28 56

112

224

7 14 28 56

112

224

Input Shape

(c) Filters = 128

Input Shape

(d) Filters = 256

Figure 3.2: Exploring the relation of TCPU/GPU with different input shapes and
filter counts. Input channels and kernel shape are 64 and 3, respectively.

GPU is always a more efficient processor regardless of the size of tensors
for fully-connected layers. However, for other layers, the more efficient
processor depends on the size of the tensors involved in the processing.
Therefore, we limit our analysis of TCPU/GPU to different parameter sizes
in convolution, normalization, and pooling layers. The normalization and
pooling layers follow a convolution layer and must execute on the same
component (to avoid significant data switching overhead) as the convo-
lution layer. Therefore, we are most interested in changes in the total
execution time (the sum of convolution, normalization, and pooling layer
execution) with changes in the parameter sizes.

There are four size variables of interest for a convolution, normalization,
and pooling layer: input shape, input channels, kernel shape, and the
number of filters. Table 3.2 indicates the size variable values we explored
in this work. We determined these values based on the layers’ parameters
in real-world CNNs. On this account, we limit our exploration to realistic
values of the size of the layer parameters. We computed TCPU/GPU for
different values of various size variables to analyze their effect on latency.

3.5 layer latency analysis

47

Table 3.2: The explored values for convolution, normalization, and pooling layer

size variables.

Size Variable

Input Shape

Input Channels

Number of Filters

Kernel Shape

Explored Values
7, 14, 28, 56, 112, 224
1, 2, 32, 64, 128, 256, 512, 1024
16, 32, 64, 128, 256, 512, 1024
3, 5, 7

Convolution

Normalization

Pooling

Total

U
P
G
/
U
P
C
T

4

3

2

1

U
P
G
/
U
P
C
T

4

3

2

1

3

5

7

3

5

7

Kernel Shape

(a) Filters = 64

Kernel Shape

(b) Filters = 128

Figure 3.3: Exploring the relation of TCPU/GPU with kernel shape for the first
convolution layer with input shape 224 and three channels. The kernel
shape has no significant effect on the value of TCPU/GPU for the
convolution layer (blue line).

Input Shape Analysis. In conventional CNNs, the input of the first
layer (image shape) is a tensor with shape 224 or 227 and decreases as
we go deeper in the network. Figure 3.2 shows the value of TCPU/GPU
by changing the input shape for a different number of filters. The input
channels and the kernel shape are 64 and 3, respectively. We analyze it
for other values of input channels and kernel shapes and observe similar
behavior. We observe by increasing the input shape, the TCPU/GPU also in-
creases. Therefore, increasing input shape makes the convolution, pooling,
and normalization layers execute faster on the GPU than on the CPU.

Kernel Shape Analysis. Most layers in CNNs have a kernel shape of 3.
Although the kernel’s shape in the initial layers may be more extensive (5
or 7). We explore the effect of changing the kernel shape for the first layer
with input shape 224 and three input channels. Figure 3.3 shows the value
of TCPU/GPU for convolution, pooling, normalization, and total timing by

48

layer-switched low latency inference

Convolution

Normalization

Pooling

Total

U
P
G
/
U
P
C
T

0.6

0.4

0.2

U
P
G
/
U
P
C
T

1

0.5

4

3

2

1

U
P
G
/
U
P
C
T

U
P
G
/
U
P
C
T

0.5

0.4

0.3

0.2

1

3

5

7

1

3

5

7

Kernel Shape

(a) Input Shape = 7

Kernel Shape

(b) Input Shape = 14

U
P
G
/
U
P
C
T

2

1

1

3

5

7

1

3

5

7

Kernel Shape

(c) Input Shape = 28

Kernel Shape

(d) Input Shape = 56

U
P
G
/
U
P
C
T

4

3

2

1

1

3

5

7

1

3

5

7

Kernel Shape

(e) Input Shape = 112

Kernel Shape

(f) Input Shape = 224

Figure 3.4: Exploring the relation of TCPU/GPU with kernel shape. We show this
exploration for different input shapes. The number of filters and input
channels is 128 and 64, respectively.

increasing the kernel shape for the different number of filters. The value
of TCPU/GPU for pooling and normalization layers is much higher than
one (GPU is preferred), and for a convolution layer, it is close to one.
For smaller kernels, the contribution of normalization and pooling layers
towards the total time is higher. We ascribe this observation to the fact
that small kernels result in fewer operations in the convolution layer but do
not help reduce them in the normalization and pooling layer. The input and
output sizes for layers remain almost the same as the kernel shape increases
or decreases. We observe that the value of TCPU/GPU for convolution is not

3.5 layer latency analysis

49

Convolution

Normalization

Pooling

Total

U
P
G
/
U
P
C
T

0.8

0.6

0.4

0.2

1

3

32

64

128

256

1

3

32

64

128

256

Input Channels

(a) Input Shape = 7

Input Channels

(b) Input Shape = 14

U
P
G
/
U
P
C
T

4

3

2

1

1

3

32

64

128

256

1

3

32

64

128

256

Input Channels

(c) Input Shape = 28

Input Channels

(d) Input Shape = 56

4

2

U
P
G
/
U
P
C
T

U
P
G
/
U
P
C
T

0.4

0.2

U
P
G
/
U
P
C
T

2

1.5

1

0.5

U
P
G
/
U
P
C
T

4

3

2

1

1

3

32

64

128

256

1

3

32

64

128

256

Input Channels

(e) Input Shape = 112

Input Channels

(f) Input Shape = 224

Figure 3.5: Exploring the relation of TCPU/GPU with the number of input channels.
We show this exploration for different input shapes. The number of
filters and kernel shape are 256 and 3, respectively.

changing significantly by increasing kernel shape. However, an increase
in the kernel shape increases the contribution of the convolution layer
in the total time, so the total time is close to the convolution time. Our
analysis shows that the value of TCPU/GPU is always larger than one (GPU
is preferred) for the first convolution layer.

There are convolution layers with a kernel shape of 1 in some models.
We explored the effect of kernel size on the value of TCPU/GPU for these
layers. Figure 3.4 shows the value of TCPU/GPU by increasing the kernel

50

layer-switched low latency inference

Convolution

Normalization

Pooling

Total

U
P
G
/
U
P
C
T

0.4

0.3

0.2

0.1

0

U
P
G
/
U
P
C
T

1.5

1

0.5

0

U
P
G
/
U
P
C
T

4

2

0

1

2

32

64

128

256

Filters

(a) Input Shape = 7

1

2

32

64

128

256

Filters

(c) Input Shape = 28

1

2

32

64

128

256

Filters

(e) Input Shape = 112

U
P
G
/
U
P
C
T

0.8

0.6

0.4

0.2

0

U
P
G
/
U
P
C
T

U
P
G
/
U
P
C
T

4

2

0

4

2

0

1

2

32

64

128

256

Filters

(b) Input Shape = 14

1

2

32

64

128

256

Filters

(d) Input Shape = 56

1

2

32

64

128

256

Filters

(f) Input Shape = 224

Figure 3.6: Exploring the relation of TCPU/GPU with the number of filters. The
figure shows this relation for different input shapes. The number of
input channels and kernel shape are 64 and 3, respectively.

Table 3.3: The preferred processing component based on size variables.

Input Shape

Input Channels

224

3

112

56

28

14

7

32

64-128

32

64

128-256

96-512

384-1024

Filters

32-96

32

64

32-64 128-256 128

256

96-512 384-1024 512-1024

Preferred Component GPU CPU GPU CPU

GPU CPU GPU CPU

CPU

CPU

3.5 layer latency analysis

51

shape for different input sizes. The number of input channels and filters is
64 and 128, respectively. This figure shows that for smaller input shapes (7
and 14), the value of TCPU/GPU for total time increases with increasing
kernel shape. On the contrary, for larger input shapes (56, 112, and 224),
the value of TCPU/GPU does not increase significantly. We analyze it for
other values for the number of input channels and filters and see similar
behavior. Therefore, the effect of kernel shape on the value of TCPU/GPU
depends on the other variables such as input shape and number of filters.
Input Channels Analysis. The input tensor of CNNs starts with three
channels, and the number increases by going deeper. Figure 3.5 shows the
value of TCPU/GPU by changing the number of input channels for different
input sizes. The number of filters and kernel size are 256 and 3, respectively.
The analysis for other values of kernel size and the number of filters exhibits
the same behavior as here. Our experiments show that for small input
shapes (less than 28), the increase in the number of input channels increases
the values of TCPU/GPU. Contrarily, for large input shapes (larger than 28),
an increase in input channels decreases TCPU/GPU. Therefore, the effect of
the number of input channels on TCPU/GPU depends on the input shape.

Filters Analysis. The filters in a layer construct the input channels for
the subsequent layer, and the number of filters usually increases as we
go deeper into the network. Figure 3.6 shows the changes in the value of
TCPU/GPU by changing the number of filters for different input sizes. The
number of input channels and the kernel shape are 64 and 3, respectively.
The analysis for other values of kernel size and the number of input
channels demonstrate similar behavior. Our experiments show that by in-
creasing the number of filters, the TCPU/GPU also increases. Consequently,
that moves the latency in support of the GPU over the CPU.

Discussion: There are many noteworthy observations in these experi-
ments. We observe an inconsistent relationship between the number of
channels and kernel shape with the value of TCPU/GPU for the convolution,
normalization, and pooling layers. However, there is a consistent relation
between the input shape and the number of filters with the TCPU/GPU;
The input shape decreases (CPU is preferred), and the number of filters
increases (GPU is preferred) as we go deeper into the networks.

Table 3.3 shows the preferred component for layers based on the size
variables. The table shows that for the first layer with input shape 224,
layers (with different number of filters) prefer the GPU, and for deeper
layers, with input shapes of 28, 14, and 7, layers prefer the CPU. However,

52

layer-switched low latency inference

GPU big CPU CPU-GPU Layer-Switched

]
s

m

[

y
c
n
e
t
a
L

100

50

0

AlexNet

GoogleNet

MobileNet

ResNet50

SqueezeNet

Figure 3.7: Inference latency for CPU-GPU layer-switched execution compared to

running the whole network with the CPU or GPU.

for middle layers with input shapes 112 and 56, the preference depends on
the other variables: the number of input channels and filters.

3.6 results

We evaluate the inference latency by finding the best mapping of layers to
components compared to running the entire network with only the CPU
or GPU. First, we measure the processing time of each layer with both the
CPU and the GPU. Second, we use the best HMPSoC component for each
layer and switch between CPU and GPU. However, each switch comes with
an overhead that increases latency. Therefore, we only switch if we expect
to improve the latency while considering the switching overhead. We use a
regression model to estimate switching overhead between the components
based on the involved data transfer size.

We measure the inference latency for different CNNs with the CPU-GPU
layer-switched execution on the Khadas VIM 3 board. This measurement
implicitly includes the switching overhead. Figure 3.7 shows the latency
of different CNNs with CPU-GPU layer-switched execution compared to
running the CNNs on only the CPU or GPU. The results show that the
layer-switched execution reduces the latency, on average, by 14.40% and
9.58% compared to CPU- and GPU-only execution, respectively. The layer-
switch execution reduces the latency by 4.72% on average compared to the
minimum CPU- or GPU-only execution.

3.7

summary

This chapter explored the execution characteristics of CNN layers on
HMPSoCs, demonstrating that some layers achieve lower latency on the

3.7 summary

53

CPU, while others benefit from GPU execution. We analyzed this behavior
based on key layer parameters and introduced CPU-GPU layer-switched
execution, a novel approach that dynamically assigns CNN layers to the
processing unit (CPU or GPU) where they execute most efficiently.

Our implementation on the Amlogic A311D HMPSoC within the Khadas
VIM3 board confirms that CPU-GPU layer-switching reduces inference
latency compared to CPU- or GPU-only execution, despite the additional
overhead introduced by inter-processor switching. By dynamically assign-
ing each CNN layer to the most efficient processing unit, our approach
directly addresses RQ1 and demonstrates that a fine-grained, heteroge-
neous execution strategy can yield measurable latency improvements while
mitigating inter-processor communication overhead.

The insights and experimental results presented here validate the ef-
fectiveness of our framework on a representative platform and establish
key design principles for optimizing latency in embedded deep-learning
systems. In the next chapter, we extend this work to explore the trade-off
between latency and total energy consumption. We analyze CNN layers
across different processing elements and frequency levels, considering the
impact of switching overhead on energy efficiency. This progression reflects
the overarching goal of achieving responsive, efficient, and robust on-device
deep learning inference.

4

P E L S I : P O W E R - E F F I C I E N T
L AY E R - S W I T C H E D I N F E R E N C E

Building on the latency optimization strategies in Chapter 3, this chapter
shifts focus to power efficiency in CNN inference on HMPSoCs while
maintaining target latency constraints. While minimizing inference latency
is crucial for real-time applications, power efficiency is equally vital, espe-
cially for battery-powered mobile and embedded devices. Achieving this
requires careful processor selection and frequency management, as CNN
layers vary in computational and power efficiency across CPU and GPU
architectures. Addressing these challenges enhances power efficiency in
deep learning inference on HMPSoCs, the core focus of RQ2.

To tackle this, we introduce PELSI, a framework that adjusts processor
selection (CPU/GPU switching) and voltage-frequency scaling (DVFS) at
the layer level to optimize power efficiency while meeting latency con-
straints. Unlike conventional approaches that use a fixed processor or
frequency, PELSI explores fine-grained optimizations per layer. It employs
a GA to efficiently search the design space of layer-to-processor mappings
and DVFS settings. Experiments on the Rock-Pi N10 platform (RK3399Pro
HMPSoC) show that PELSI improves power efficiency by 44.48% over state-
of-the-art methods, highlighting the benefits of joint processor selection and
DVFS tuning for energy-efficient inference on resource-constrained devices.

This Chapter is based on:

• E. Aghapour, D. Sapra, A. Pimentel, A. Pathania "PELSI: Power-Efficient
Layer-Switched Inference" [45], in IEEE 29th International Conference on Embed-
ded and Real-Time Computing Systems and Applications (RTCSA), 2023
Candidate for Best Paper Award

55

56

pelsi: power-efficient layer-switched inference

6 DVFS Levels

8 DVFS Levels

5 DVFS Levels

LITTLE CPU

A53 Core

A53 Core

A53 Core

A53 Core

L2 Cache

big CPU

Mali-T860 MP4 GPU

A72 Core

A72 Core

Core

Core

L2 Cache

L2 Cache

CCI Bus

DRAM

Figure 4.1: An abstract block diagram of RK3399Pro HMPSoC in RockPi N10 em-

bedded platform.

4.1

introduction

Computer vision tasks are now integral in many high-performance em-
bedded applications across domains such as autonomous driving [22],
intelligent robotics [23], image classification [16], and object detection [24].
CNN kernels processing (inference) image streams to extract recognizable
features accurately are used extensively for computer vision tasks in embed-
ded platforms. CNNs are increasingly inferencing higher resolution image
streams streaming at ever-increasing frame rates. Nevertheless, privacy and
performance constraints mandate the inference on the embedded platforms
themselves. Embedded platforms, however, are more severely constrained
in terms of their power consumption than their non-embedded counter-
parts. Therefore, the success of embedded computer vision applications
hinges on the platforms to provide low-power, low-latency CNN inference.
HMPSoCs nowadays power most high-end embedded platforms. Fig-
ure 4.1 illustrates the modern RK3399Pro HMPSoC within the Rock-Pi N10
embedded platform. It comprises two multi-core CPU clusters – LITTLE
and big, and an embedded multi-core GPU. DVFS technology allows the
HMPSoC components (CPU clusters and GPU) to run independently at
different frequencies [46, 47]. Furthermore, all the HMPSoC components
are capable of performing CNN inference [27]. Therefore, DVFS allows
a trade-off between inference performance and inference power on all
HMPSoC components. The power efficiency of a CNN layer depends upon
the interaction between the memory-compute characteristics of the layer
and the underlying HMPSoC component. Consequently, there is a wide
power-efficiency spectrum wherein one can perform a CNN inference on
HMPSoCs, as shown in Figure 4.2. Figures 4.2 (a) and 4.2 (b) show changes

4.1 introduction

57

LITTLE

big

GPU

100

300

500

700

900

1,100

1,300

1,500

1,700

1,900

HMPSoC Component Frequency [MHz]

(a) Compute-Intensive Convolution Layer

LITTLE

big

GPU

100

300

500

700

900

1,100

1,300

1,500

1,700

1,900

HMPSoC Component Frequency [MHz]

(b) Memory-Intensive Fully-Connected Layer

]
t
t
a
W
/
S
P
F
[

y
c
n
e
i
c
fi
f
E
r
e
w
o
P

6

4

2

]
t
t
a
W
/
S
P
F
[

y
c
n
e
i
c
fi
f
E
r
e
w
o
P

14

12

10

8

Figure 4.2: Power efficiency of different CNN layers (from AlexNet) in different

HMPSoC components at different frequencies.

Target CNN Inference Latency

big CPU
b f2
f1

b f3
b

t
u
p
n
I

1
r
e
y
a
L

2
r
e
y
a
L

3
r
e
y
a
L

Data

GPU
f4
g

4
r
e
y
a
L

big CPU
f5
b

Data

Data

5
r
e
y
a
L

LITTLE CPU

f6
l

6
r
e
y
a
L

f7
l

f8
l

7
r
e
y
a
L

8
r
e
y
a
L

t
u
p
t
u
O

Figure 4.3: An abstraction depicting power-efficient CPU-GPU layer-switched

CNN inference employed within PELSI framework.

in power efficiency with frequency change on different HMPSoC com-
ponents for a compute-intensive convolution layer and memory-intensive
fully-connected layer, respectively.

The power-efficiency spectrum widens further with the possibility of
performing CPU-GPU layer-switched inference on HMPSoCs. As discussed
in Chapter 3, we were the first to show that heterogeneous layers within a
CNN exhibit performance heterogeneity on embedded CPUs and GPUs.
We demonstrated that some layers execute faster on the embedded CPU

58

pelsi: power-efficient layer-switched inference

Table 4.1: The size of design space for power-efficient CPU-GPU layer-switched
inference for different CNNs with different numbers of partitionable
layers on RK3399Pro HMPSoC.

CNN

Partitionable Layers Number of Design Points

AlexNet

GoogleNet

MobileNet

ResNet50

SqueezeNet

8

11

14

18

10

1.7e+10

1.2e+14

8.0e+17

1.0e+23

6.1e+12

while others execute faster on the embedded GPU. Based on this obser-
vation, we proposed a framework to switch between CPU and GPU mid-
inference based on the executing layer for maximizing the performance of
CNN inference. We showed that even after accounting for the overhead of
switching between CPU and GPU back-and-forth, the observed latency of
CNN inference was lower than executing purely on either of the HMPSoC
components. However, we did not explore DVFS with layer-switched infer-
ence and run their CPU and GPU only at their maximum frequencies for the
highest inference performance. But execution only at the highest frequency
results in a high-power inference. Combining CPU-GPU DVFS with CPU-
GPU layer-switched inference allows for a fine-grained trade-off between
the CNN inference performance and power consumption under a given
latency constraint. Note, the layer-switched inference design is distinct from
pipelined CNN inference design [29].

We introduce a novel framework, PELSI, that explores the idea of
power-efficient CPU-GPU layer-switched inference, as shown in Figure 4.3.
CNN inference under PELSI switches between HMPSoC components mid-
inference depending upon the CNN layer under execution. PELSI simul-
taneously sets the layer-wise frequency of the HMPSoC component to the
level that allows the CNN to achieve its target latency most power efficiently.
PELSI operates within a large exponential design space. HMPSoC with FB,
FL, and FG DVFS frequency levels for its big CPU, LITTLE CPU, and GPU
projects a design space of size (FL + Fb + FG)N for a CNN with N parti-
tionable layers. Table 4.1 shows the design space size for different CNNs
on a RK3399Pro HMPSoC. It is computationally infeasible to exhaustively
search this design space for an optimal solution. Therefore, PELSI includes
a GA to identify a near-optimal solution for power-efficient CPU-GPU layer-
switched inference under latency constraints.

4.1 introduction

59

]
t
t
a
W
/
S
P
F
[

y
c
n
e
i
c
fi
f
E
r
e
w
o
P

1.8

1.6

1.4

LITTLE

big

GPU

LITTLE-LW

big-LW

GPU-LW

PELSI

Figure 4.4: Power efficiency of MobileNet running on LITTLE CPU, big CPU,
and GPU with fixed DVFS (LITTLE, big, and GPU), layer-wise DVFS
(LITTLE-LW, big-LW, and GPU-LW), and the proposed PELSI framework
under a given latency constraint of 200 ms

.

Motivational Example: We perform a CNN inference with MobileNet
with a target latency of 200 ms as a motivational example. Figure 4.4
shows the power efficiency of CNN inference that meets the target latency
with different executions. The CNN inference attains a power efficiency
of 1.49 FPS/Watt, 1.33 FPS/Watt, and 1.29 FPS/Watt while executing at the
lowest possible fixed frequency that meets the target latency using only
LITTLE CPU, big CPU, and GPU, respectively.

We now allow layer-wise DVFS for single-component CNN inference
and use a configuration that meets the target latency. However, we run
different CNN layers at different frequencies to maximize the inference’s
power efficiency on a single HMPSoC component. Figure 4.4 shows that the
CNN inference attains a power efficiency of 1.79 FPS/Watt, 1.62 FPS/Watt,
and 1.37 FPS/Watt when executing layer-wise DVFS that meets the target
latency while using LITTLE CPU, big CPU, and GPU, respectively. Using
layer-wise DVFS increases the power efficiency of inference by 20.00%,
21.89%, and 6.27% against fixed-frequency inference on LITTLE CPU, big
CPU, and GPU, respectively.

Finally, in our motivational example, we allow layer-wise DVFS alongside
switching between HMPSoC components mid-inference as proposed
with PELSI. Figure 4.4 shows that CNN inference under PELSI attains
a power efficiency of 1.89 FPS/Watt for the same target latency. PELSI
increases the power efficiency of CNN inference by 6.26%, 17.43%, and
38.42% against single-component layer-wise DVFS CNN inference on
LITTLE CPU, big CPU, and GPU, respectively. Therefore, our motivational

60

pelsi: power-efficient layer-switched inference

example motivates using layer-wise DVFS synergistically with HMPSoC
component-switching for extracting maximum power efficiency for a
latency-constrained CNN inference.

Our Novel Contributions: We make the following novel contributions in

the context of this work.

• We propose a framework, PELSI, that explores the idea of power-

efficient CPU-GPU layer-switched CNN inference.

• We propose a GA within PELSI to identify a near-optimal configu-
ration for power-efficient CPU-GPU layer-switched CNN inference
under latency constraints.

• We implement the proposed PELSI framework within the ARM-CL

and evaluate it using RK3399Pro HMPSoC.

Open Source Contribution: PELSI is publicly available for download at
https://github.com/Ehsan-aghapour/ARMCL-pipe-all ("CPU-GPU-LW" branch).

4.2 related work

Efficient power management has always been a consideration for resource-
constrained embedded devices. In this respect, various hardware-based
techniques have been proposed, from power monitoring [48] and power
modeling [49] for off-the-shelf hardware to creating special low-powered
hardware [50]. However, only hardware-level techniques can not effec-
tively minimize power consumption unless accompanying software-level
techniques exploit application domain-specific knowledge for power effi-
ciency [51]. We formulate PELSI with CNN-specific knowledge considera-
tions and its per-layer behavior on different computing resource types.

Several works improve power efficiency for CNN training [52, 53]. How-
ever, a trained CNN deployed on an embedded device for a long duration
will benefit more from the power efficienct inference. Another popular
direction to achieve power efficiency during CNN inference is to search
for appropriate CNN models through NAS algorithms [54]. In principle,
PELSI is orthogonal to such techniques. One can use PELSI for an efficient
layer-switched inference for a CNN designed through NAS methodologies.
Traditionally, in HPC, CNN inference is performed solely on GPUs.
Therefore, multiple works only focus on power efficiency for inference on
GPUs, such as [55] and [56]. PELSI, on the other hand, focuses on HMPSoCs
where embedded CPUs and GPUs are comparable in performance, and

4.3 setup

61

Table 4.2: The available DVFS levels of the LITTLE CPU, big CPU, and GPU on

RK3399Pro HMPSoC.

LITTLE CPU

big CPU

GPU

Frequency (MHz)

Voltage (mV)

Frequency (MHz)

Voltage (mV)

Frequency (MHz)

Voltage (mV)

408

600

816

1008

1200

1416

800

800

850

925

1000

1125

408

600

816

1008

1200

1417

1608

1800

800

800

825

875

950

1025

1100

1200

200

300

400

600

800

800

800

825

925

1100

both are used for inference to maximize efficiency. To this end, a few
works [57] propose to analyze the power efficiency of CNN inference on
HMPSoCs for both CPUs and GPUs. The authors of [49] propose a per-
core power model, while the authors of [58] analyze power-performance
profiles of various CNNs for CPU and GPU platforms. However, unlike
PELSI, these papers do not propose any tangible solution to improve power
efficiency through hardware-software co-design.

DVFS is well-known as an efficient methodology for power management
on embedded devices. For example, [55] reduces the energy consumption of
CNN training on a GPU by controlling its operational frequency. AOA [59]
coordinates the frequency of both CPU and GPU to improve performance
and reduce total energy consumption. AOA achieves this by balancing the
workload at a higher abstraction level and does not delve deeper into the
working of a CNN and its layers.

4.3

setup

We use Rock-Pi N10 embedded platform in this work. An RK3399Pro
HMPSoC, as shown in Figure 4.1, powers the Rock-Pi N10 platform. The
platform has a hexa-core asymmetric ARM big.LITTLE multi-core CPU with
two CPU clusters – big and LITTLE. The LITTLE CPU cluster contains
four low-power, low-performance A53 cores with six DVFS levels. The big
CPU cluster contains two high-performance, high-power A72 cores with
eight DVFS levels. It also has an ARM dual-core Mali T860 GPU with six

62

pelsi: power-efficient layer-switched inference

Rock-Pi

ARM-CL
Input
L1
L2
L3
L4
Output

l

a
n
g
S

i

INA260
Ω

Power Supply

SCL

SDA

ARDUINO

Read Power

GPIO

Read Annotation

Write

Annotated
Power Samples

Latencies

Host

Profile Data

Figure 4.5: An abstract diagram depicting setup for CNN inference layer-level

power profiling.

DVFS levels. Table 4.2 summarizes all the DVFS levels available for different
components in the RK3399Pro HMPSoC. A 4 GB LPDDR4 acts as the main
memory for the HMPSoC running Android v9.0 with kernel v4.9.

We use ARM-CL v21.02 in this work for CNN inference. We use AlexNet,
GoogleNet, MobileNet, ResNet50, and SqueezeNet as the CNN kernels. These
CNNs perform image classification. Their designers trained them on the
ImageNet data set for 1000 image classes. The input to these models are
images of size (224 × 224) with three channels (RGB), and the output is a
tensor of size 1000 predicting the input image’s class. We implement the
GA using NSGA2 employing the pymoo Python3 library.

We use an external power data acquisition setup for fine-grained CNN
inference power consumption measurements on Rock-Pi N10, as shown in
Figure 4.5. The setup uses an INA260 sensor that measures the current and
voltage transfer over a single I2C interface. We pass the power supply for
the Rock-Pi N10 through an INA260 sensor, wherein the sensor measures
the current based on dropped voltage with an internal shunt resistor. An
Arduino Uno embedded board samples voltage and current readings from
the INA260 sensor through an I2C clock and data pins (SCL and SDA) at the
sampling rate of 692 samples per second. Arduino Uno sends the data to
the host laptop for further processing over the serial port. The setup allows
the annotation of the power data with meta-data using signals passed from
the Rock-Pi N10 through GPIO pins to the Arduino Uno. We modify ARM-
CL to send a signal (with meta-data) at the start and end of the execution
of each layer of the CNN. The meta-data then allow us to separate the
power consumption of each layer of CNN during an inference. We get the
corresponding layer latency from ARM-CL using clock functions.

4.4 implementation

63

User Space

ARM-CL

L1

L2 L3

L4

L5

ioctl

f1
b

g f3
f2
g

f4
l

f5
b

Kernel Space

GPU DVFS

set_freq(fg)

Kernel Governor

set_freq(fb)

big DVFS

set_freq(fl)

LITTLE DVFS

Figure 4.6: An abstraction depicting the implementation of PELSI.

4.4

implementation

We implement the proposed PELSI framework within the ARM-CL frame-
work. ARM-CL is a collection of low-level (written in Assembly language)
ML functions. They come highly optimized for the ARM Cortex-A CPU and
Mali GPU cores. ARM-CL forms the ideal choice to perform CNN inference
for our setup. Power-efficient CPU-GPU layer-switched CNN inference
involves implementing two new features – HMPSoC component-switching
and layer-wise DVFS – not available by default in the ARM-CL.

In Chapter 3, we extensively extend ARM-CL to support HMPSoC com-
ponent switching and make these extensions publicly available. We build
upon this extended open-source version of ARM-CL, which enables HMP-
SoC component switching out-of-the-box, as the foundation for this work.
Further, we introduce additional extensions to this ARM-CL version to sup-
port orthogonal layer-wise DVFS, enabling the proposed PELSI. Figure 4.6
illustrates the implementation of layer-wise DVFS working synergistically
with component switching within PELSI.

It is common practice to use pseudo file system sysfs provided by the
Linux kernel to change the frequency of HMPSoC components (CPU or
GPU cores) from the OS user space. However, there is higher overhead
when changing an HMPSoC component’s frequency using sysfs than from
within the OS kernel space. Therefore, PELSI updates the frequencies for
layer-wise DVFS change from within the kernel space to make layer-wise
DVFS time-wise feasible.

The CNN inference happens in the user space. Therefore, the information
when a CNN layer starts/finishes execution is only available in the user
space. This information must get passed down to the kernel space to
perform synchronized layer-wise DVFS with minimal overhead. We embed
ioctl calls (written in C/C++) at the start of the execution of every CNN
layer in ARM-CL that signal the execution frequency for the layer’s pre-

64

pelsi: power-efficient layer-switched inference

Table 4.3: The min and max DVFS delay (µs) for the Little CPU, big CPU, and GPU
on RK3399Pro HMPSoC, when transitioning to higher (up) and lower
(down) frequency levels.

Transition

PE Min Delay

Frequency

Max Delay

Frequency

Up

Down

L

B

G

L

B

G

296

193

657

109

91

670

i

0

0

0

4

7

4

i+1

1

1

1

3

3

1

i

0

6

2

3

4

4

i+1

2

7

4

0

1

2

4211

3811

4461

193

1413

1464

ferred HMPSoC component. A custom power Governor of our design (em-
bedded within the kernel source code) receives this signal in the kernel
space. It then sets the frequency of the preferred HMPSoC component to
the value within the received signal. Simultaneously, to minimize power
consumption, it sets the frequency of the non-preferred (idle) HMPSoC
components to the minimum value. The involved ioctl calls are non-
blocking. The low overhead allows for fast layer-wise DVFS.

During experiments, we observe a noticeable delay from initiating a
frequency update to the actual change in the hardware. This delay varies
for different frequency levels for all components. Table 4.3 shows the min-
imum and maximum frequency transition delay (µs) when increasing (up
transition) and decreasing frequency (down transition). PELSI accounts for
these delays in computing the execution time and power of a layer.

4.5 algorithm

PELSI, as shown in Figure 4.3, requires the determination of the preferred
HMPSoC component and the component’s corresponding layer-wise fre-
quency for every CNN layer. PELSI must ensure meeting the inference’s
latency target with maximum power efficiency. PELSI targets an NP-hard
optimization problem with a large exponential design space, as shown
in Table 4.1. Consequently, it is impossible to brute-force the optimal
power-efficient CPU-GPU layer-switched CNN inference configuration in
PELSI. Therefore, we propose to use a GA within PELSI to find a near-
optimal configuration that meets a given CNN inference target latency with

4.5 algorithm

65

Chromosome

(c1, f1) (c2, f2)

...

(cN, fN)

Figure 4.7: Chromosome gene encoding representing the HMPSoC component
type (ci) and the corresponding component frequency (fi) for every
layer i in CNN with N layers.

minimal power consumption. The GA accounts for the power-performance
overhead of switching components mid-inference inherent in PELSI. The
implementation overhead for achieving fine-grained layer-level DVFS in
PELSI (Figure 4.6) is negligible. Therefore, the GA does not take it into
account for optimization.

It takes up to a minute to determine the power-performance attributes
for a configuration in PELSI directly from the embedded platform. The GA
within PELSI requires an evaluation of hundreds of thousands of such con-
figurations. Consequently, it is time-wise infeasible (though technically pos-
sible using our setup) to run the GA directly with live power-performance
feedback from the embedded platform. Therefore, we instead execute our
GA using power-performance profiled data for every CNN layer at different
HMPSoC components at different frequencies obtained using the data
acquisition setup shown in Figure 4.5. We use a linear regression model that
correlates the size of data migration (between the components on switching)
with the observed power and performance penalty to determine the power-
performance overhead of component switching involved in a configuration.
This evaluation design allows the GA to find a near-optimal configuration
in a reasonable amount of time at the cost of introducing a minimal error
between the expected and observed power-performance attributes of the
solution configuration when ported to the real embedded platform.

GA is a meta-heuristic design-space exploration algorithm based on the
process of natural evolution. The proposed GA is an iterative algorithm
that begins with encoding some configurations into chromosomes. Each
distinct chromosome represents a unique individual. All the individuals
together form the initial population. After evaluating the population, using
a fitness function based on CNN inference latency and power consumption,
the weak (and unviable) individuals are replaced with the offspring of the
stronger individuals produced through mating (crossover and mutation)
functions. This process continues over multiple iterations. Therefore, the
population in later iterations will consist of fitter individuals representing
more power-efficient latency-meeting configurations than the configura-

66

pelsi: power-efficient layer-switched inference

Parent1

(c1, f1) (c2, f2) (c3, f3) ... (cN, fN)

(c1, f1) (c2, f2) (c ′

3) ... (c ′

N, f ′

N)

Child1
3, f ′

(c ′

1, f ′

1) (c ′

2, f ′

2) (c ′

3) ... (c ′

N, f ′

N)

Parent2
3, f ′

Child2

(c ′

1, f ′

1) (c ′

2, f ′

2) (c3, f3) ... (cN, fN)

(a) Crossover

Child

Mutated Child

(c1, f1) (c2, f2) (c3, f3) ... (cN, fN)

(c1, f ′

1 ) (c2, f2) ( c ′

3 , f3) ... (cN, fN)

(b) Mutation

Figure 4.8: An abstraction illustrating the mating process using crossover and
mutation within the proposed GA for a CNN with N layers.

tions that formed the initial population. The process eventually converges
to the solution population when the GA can not produce stronger offspring.
Population: The population contains individuals with a single chromo-
some representation of configurations. Figure 4.7 shows the gene encoding
for a chromosome within an individual. There is a gene for every layer
in the CNN under inference. The gene contains the information about
the HMPSoC component and the corresponding frequency with which the
layer will execute on the HMPSoC. The chromosome, therefore, contains all
the information necessary to determine the power-performance attribute of
its underlying configuration.

Fitness function: A fitness function evaluates and ranks the offspring
based on an optimization objective while operating under CNN inference
latency constraint. The optimization objective for the GA is to minimize
the energy consumption per inference. Measuring the onboard energy
consumption for each design point takes a long time. Therefore, to converge
within a reasonable time frame, we use profiles of the time and power
consumption for layers of CNN when running on LITTLE CPU, big CPU,
and GPU at all frequency levels. The fitness function estimates the layer-
wise energy consumption and inference latency using a regression model
on the profiled data. Moreover, there is a transition delay by the request
to switch frequency while the layer has already started to execute. This
delay leads to part of the layer executing in the old frequency until the new
frequency is active in the hardware.

The energy estimation model accounts for various factors of the DVFS-
based layer-switched inference of a CNN. The final estimation estimates
power consumption and timing analysis of per-layer execution, the transi-

4.5 algorithm

67

tion delay, and the communication overhead to switch between different
processing components. We investigate the correctness of the energy con-
sumption estimation function by measuring the actual values from 1000
random design points and comparing them against estimated values. The
overall mean error rate between estimated and measured values remained
between 6.16% and 9.32% for different CNN models.

Selection: After evaluating and ranking the population, the GA selects
n parents ( n
2 pairs) using a binary tournament selection algorithm to
generate offspring with mating operations. In binary tournament selection,
two individuals are randomly selected from a population and compared
with each other. The GA then selects the individual with higher fitness as
one of the parents for the next generation. It repeats the tournament (with
the previously selected parent excluded) to find the other parent. The
GA then marks the two selected parents as a mating pair. An individual
can be in multiple mating pairs. Therefore, a stronger individual within
the population has a higher probability of spawning more offsprings. The
selection process repeats till the GA selects the desired mating pairs.

Mating: The GA uses crossover and mutation operations to generate off-
spring from the selected parents, as shown in Figure 4.8. For the crossover
operation, the GA selects a random crossover point in the chromosome and
generates two offspring by combining the first and second sections of each
pair, as shown in Figure 4.8 (a). Therefore, for the offspring produced from
the crossover, one parent determines the HMPSoC component mapping
and the corresponding DVFS settings for the first section. Complemen-
tarily, the other parent determines the mapping and DVFS setting of the
second section. After generating offspring, the GA applies mutation by
selecting a random gene (layer) and changing its first value (target HMPSoC
component), and selecting another random gene and changing its second
value (DVFS settings), as shown in Figure 4.8 (b).

Survival: The mating process generates an offspring population Qi in
GA iteration i. The offspring population Qi is the same size n as the parent
population Pi, as each pair of parents generates exactly two offspring. The
GA then merges the offspring population Qi with the parent population
Pi to generate the merged population Ri. It then ranks the individuals in
the merged population Ri according to their fitness. The GA then selects
the top n individuals from Ri to form the next parent generation Pi+1,
corresponding to the GA iteration i + 1. This process ensures that the parent
generation Pi+1 could not be worse in terms of fitness than the parent
generation Pi in the previous iteration.

68

pelsi: power-efficient layer-switched inference

Convergence: The process of selection, followed by mating, and survival
repeats iteratively in the GA. In each iteration with crossover, the GA
explores different areas of design space. In each iteration with mutation, the
GA attempts to find better design points within an area. The GA achieves
convergence when it is no longer possible to produce stronger (yet viable)
offspring from a given generation of parents. The GA reports the top-
ranked individual as the solution on convergence. Within this individual’s
chromosome resides the near-optimal power-efficient configuration that
meets the given latency constraint.

4.6 results

We evaluate our proposed PELSI framework on the Rock-Pi N10 embedded
platform, which features the RK3399Pro HMPSoC. Since the work presented
in Chapter 3, which introduced the concept of CPU-GPU layer-switched
execution, does not incorporate DVFS and focuses solely on maximizing
performance, a direct comparison in terms of power efficiency would not be
fair. The work most similar to PELSI is AOA [59]. The original AOA utilizes
DVFS at run-time based on the power and utilization of HMPSoC compo-
nents to minimize total energy consumption during a CNN inference. We
modify AoA to improve power efficiency under a latency constraint similar
to PELSI for a baseline comparison. We call the baseline AoA-like.

AOA comprises two parts. The first part works on the power consump-
tion of the current interval and the CPU-GPU utilization. AOA in the first
part determines if it can increase the frequency of processors while keeping
the total energy consumption as the constraint. In the second part, AOA
computes an imbalance factor representing the CPU and GPU utilization
difference. When this factor outweighs a threshold, it triggers the imbalance
state. In the imbalance state, the bottleneck processor’s frequency increases
till it reaches the maximum level. Otherwise, AOA decreases the frequency
of the non-bottleneck processor.

We design the AOA-Like algorithm by modifying the first part of the
original AOA. AOA preserves total energy consumption, whereas the AOA-
Like has to meet the latency deadline. For this purpose, after each layer
execution, AOA-Like decides if the frequency of a component is worth
increasing to meet the target latency. We measure the execution time of
CNN layers with all fixed frequency combinations of GPU and its host (big
CPU) to compute the average execution time per layer. With this data, AOA-
Like assign every layer a task-portion number, which is the percentage of

4.7 summary

69

AOA-Like

PELSI

AlexNet

GoogleNet

MobileNet

ResNet50

SqueezeNet

]
t
t
a
W
/
S
P
F
[

y
c
n
e
i
c
fi
f
E
r
e
w
o
P

2

1.5

1

0.5

0

Figure 4.9: Normalized CNN inference power-efficiency for PELSI against the

state-of-the-art for different CNNs.

time taken by the layer within the overall inference time. The total task-
portion number of remaining layers is then compared with the remaining
percentage of time left in the target latency (time-portion). If the ratio of the
total task portion to the time portion is higher than one, the frequency level
is increased by the same number of steps as this ratio. The second part of
AOA-Like remains unchanged to keep the CPU and GPU balance.

We evaluate the improvement in the power efficiency with PELSI over
AOA-Like design with five CNNs. For the target latency of each CNN,
we add approximately 100 ms to the minimum latency that the AOA-Like
design achieves. Figure 4.9 depicts the power efficiency of PELSI against
the AOA-Like for different CNNs. It demonstrates that for all evaluated
CNNs, the PELSI achieves higher power efficiency. These power efficiency
improvements are 33.40%, 34.09%, 74.74%, 31.41%, and 48.73% for AlexNet,
GoogleNet, MobileNet, ResNet50, and SqueezeNet, respectively. Across all
CNNs, the PELSI improves power efficiency by 44.48% on average.

4.7

summary

This chapter introduced PELSI, a framework designed to optimize power
efficiency in CNN inference on HMPSoCs while maintaining target latency
constraints. We demonstrated that different CNN layers exhibit varying
power efficiency across different processors and that DVFS settings signif-
icantly influence power consumption. To address these challenges, PELSI
integrates CPU-GPU layer-switching with per-layer frequency tuning, en-
suring that CNN inference is executed in the most power-efficient config-
uration without exceeding latency constraints. To efficiently determine the
optimal DVFS settings and per-layer execution configurations, we designed
an exploration approach using a GA, allowing PELSI to systematically

70

pelsi: power-efficient layer-switched inference

search the large design space of execution strategies and identify config-
urations that maximize power efficiency for a given latency target.

Our evaluation on the Rock-Pi N10 embedded platform (RK3399Pro HMP-
SoC) shows that PELSI improves power efficiency by 44.48% compared
to state-of-the-art fixed-frequency methods. The results highlight the im-
portance of per-layer execution strategies combined with DVFS tuning in
achieving energy-efficient deep learning inference on enddevices.

While this chapter focused on optimizing latency and power consump-
tion in CPU-GPU execution, which remains the most common architecture
in end devices, the increasing adoption of NPUs in modern end devices
introduces new considerations. NPUs offer significant performance and
power efficiency gains, but their reliance on quantization can lead to
accuracy degradation. This shift from CPU-GPU designs to architectures
incorporating NPUs brings new challenges in maintaining accuracy while
leveraging power-efficient execution. The next chapter explores how NPUs
can be integrated alongside CPUs and GPUs to navigate these accuracy-
power-performance trade-offs in deep learning inference.

5

P I Q I : PA R T I A L LY Q U A N T I Z E D
D N N I N F E R E N C E O N H M P S O C S

Building on previous optimizations, this chapter tackles efficient deep
learning inference under accuracy constraints. Many modern HMPSoCs
integrate NPUs for power- and performance-efficient quantized inference.
However, full quantization may not meet accuracy requirements, while full-
precision execution on CPUs and GPUs, though more accurate, is far less
efficient. This trade-off highlights the challenge of maximizing efficiency
without sacrificing accuracy. Addressing these challenges contributes to
RQ3, which explores leveraging NPUs to balance accuracy, performance,
and power in end devices.

To tackle this, we introduce PiQi, a framework that assigns DNN layers
to CPUs, GPUs, or NPUs, enabling selective quantization. Instead of just
switching processors, PiQi determines which layers should remain full pre-
cision and which can be quantized for efficiency. To explore layer quantiza-
tion, processor mapping, and DVFS settings, PiQi employs a multi-objective
GA to find Pareto-optimal configurations under accuracy constraints. To
accelerate search, it integrates a neural network-based accuracy predictor
for rapid evaluation. Experiments on the Rock-Pi N10 (RK3399Pro HMPSoC)
show PiQi significantly improves the power-performance Pareto frontier,
outperforming state-of-the-art methods in accuracy-constrained scenarios.

This Chapter is based on:

• E. Aghapour, Y. Shen, D. Sapra, A. Pimentel, A. Pathania "PiQi: Partially
Quantized DNN Inference on HMPSoCs" [60],
in Proceedings of the 29th
ACM/IEEE International Symposium on Low Power Electronics and Design, 2024

71

72

piqi: partially quantized dnn inference on hmpsocs

Figure 5.1: Abstract block diagram of the RK3399Pro HMPSoC.

5.1

introduction

DNNs are now commonplace in computer vision applications in embedded
end devices [61]. HMPSoC platforms powering these end devices allow
for local on-chip DNN inference (without cloud support) for improved
performance and privacy [57]. HMPSoCs ship with multiple inference-
capable components such as CPUs and GPUs [62]. Moreover, state-of-the-
art HMPSoCs are increasingly shipping with NPUs for DNN inference, as
shown in Figure 5.1 for the RK399Pro HMPSoC.

NPUs are ASICs that allow for low-latency, low-power on-chip infer-
ence [63]. Figure 5.2 shows the NPU provides a several-fold increase in
inference power efficiency over a quad-core Cortex-A53 CPU, dual-core
Cortex-A72, and quad-core Mali-T860MP4 GPU running at peak frequency
within an RK399Pro HMPSoC. However, the NPU, similar to most other
NPUs in the market, can perform INT8 quantized inference but at the cost
of an accuracy loss from quantization. On the other hand, a Cortex-A53
LITTLE CPU, Cortex-A72 big CPU, and Mali-T860MP4 GPU can perform
FP32 full-precision inference but with a magnitude lower power efficiency
than the NPU. CPUs and GPUs can also perform quantized inference, but it
only brings an accuracy loss with minimal gains in power efficiency relative
to quantization with an NPU. Figure 5.3 shows the top-1 inference accuracy
loss from INT8 quantized inference against full-precision inference for
different DNNs. The figure shows AlexNet and GoogleNet experience a
minimal drop in accuracy due to quantization, while YoLov3 and MobileNet
experience a significant accuracy drop.

Full-Precision DNN InferenceQuantized DNNInferenceCortex A-53 CPUCortex A-72 CPUMali-T860MP4 GPUNPUDVFSCoreCoreCoreCoreL2 CacheDVFSDVFSCoreCoreL2 CacheCoreL2 CacheCoreCoreCoreRK3399 Pro HMPSoC5.1 introduction

73

Cortex-A53 CPU Cortex-A72 CPU Mali-T860MP4 GPU NPU

AlexNet

GoogleNet

MobileNet

YoLov3

y
c
n
e
i
c
fi
f
E
r
e
w
o
P

.

m
r
o
N

15

10

5

0

Figure 5.2: Power efficiency of different HMPSoC components with different

DNNs on RK3399Pro HMPSoC.

]

%

[

s
s
o
L
y
c
a
r
u
c
c
A

4

3

2

1

0

AlexNet

GoogleNet

MobileNet

YoLov3

Figure 5.3: Top-1 Accuracy loss for different DNNs with INT8 quantized inference

over FP32 full-precision inference.

DNNs contain several heterogeneous layers. In default inference imple-
mentations, all DNN layers execute with full precision on the CPU and
GPU or with quantization on the NPU. Consequently, if the accuracy
requirement imposed by the user is higher than the accuracy with the
NPU, then the system must employ inefficient CPU- or GPU-only inference
to meet the accuracy constraint. Therefore, we present PiQi, a framework
enabling the partial quantized inference on HMPSoCs for the first time.
PiQi allows some DNN layer execution with full precision on CPU or
GPU, whereas others execute quantized on the NPU. PiQi implements low-
overhead mid-inference layer-level switching between CPU, GPU, and NPU
to support partially quantized DNN inference.

Motivational Example: Figure 5.4 shows the Power-Performance Pareto-
optimal front for the YoLov3 DNN under a 66% accuracy constraint for
various executions. An accuracy constraint refers to the minimum level of
user-defined accuracy that the final inference must achieve to meet oper-
ational requirements. The accuracy (mAP) range for this model is 64.7%
(fully quantized) to 68.7% (full precision). For the motivational example,

74

piqi: partially quantized dnn inference on hmpsocs

LITTLE CPU-Only

big CPU-Only

GPU-Only

Partial Quantization

Accuracy Constraint = 66%

20

15

10

5

]
c
e
S
[

y
c
n
e
t
a
L

3.5

4

4.5

5

5.5

6

6.5

7

7.5

Average Power Consumption [W]

Figure 5.4: Power-Performance Pareto-front under different executions for YoLov3

DNN under an accuracy constraint.

we select a midrange target accuracy (66%) to explore the potential trade-
offs between accuracy, power consumption, and latency. Since the NPU
achieves only 64.7% with fully quantized inference, NPU-only quantized
DNN inference is not feasible under the 66% constraint.

Figure 5.4 shows that even though full-precision CPU- or GPU-only
DNN inference satisfy the accuracy constraint, the corresponding power-
performance Pareto-fronts provide sub-optimal trade-offs between power
and performance. The sub-optimality remains significant even with power-
performance trade-offs enabled by CPU and GPU DVFS in CPU- and
GPU-only DNN inference, respectively. Figure 5.4 shows the near-optimal
power-performance Pareto-front with PiQi using partially quantized DNN
inference. Figure 5.4 shows that by synchronized use of CPU, GPU, and
NPU during inference, along with CPU and GPU DVFS, PiQi provides a sig-
nificantly better power-performance trade-off than any single-component
DNN inference. While reducing power consumption and execution time
leads to lower energy consumption, our decision to optimize both power
and time objectives reflects a holistic approach that captures a broader
optimization landscape. By presenting the Pareto front of power and perfor-
mance, we offer users diverse design options, each representing an optimal
trade-off between power consumption and execution time. This approach
addresses energy concerns and provides nuanced insights, empowering
users to select the design point that aligns with their constraints.

Novel Contributions: We make the following novel contributions in the

scope of this work.

• We introduce the PiQi framework that enables partially quantized
DNN inference on HMPSoCs by implementing layer-level switching
between CPU, GPU, and NPU.

5.2 related work

75

• We characterize the power, performance, and accuracy of DNNs
under partial quantization and then build models to predict these
attributes under multi-layer partial quantization.

• We provide a multi-objective GA for determining a Power-Performance
Pareto-front with partial quantization under an accuracy constraint.

Open-Source Contributions: The code for the PiQi is publicly available
at https://github.com/Ehsan-aghapour/PiQi under MIT license. It utilizes the
ARM-CO-UP framework described in [64].

5.2 related work

Quantization [65] is a pivotal technique in DNN inference for enhancing
latency and energy efficiency on end devices in the literature. Notable
studies in [66] and [67] have honed model accuracy through per-layer
quantized weight optimization. The authors of [68] and [69] have furthered
this by incorporating quantization noise into DNN training to fine-tune
weights via stochastic gradient descent, minimizing accuracy loss. The
authors of [70] addressed quantization-induced errors through dynamic
compensation, albeit adding extra fix-point representation complexity. The
authors of [71] provided a performance characterization for quantization
on end devices, employing FP16/INT8 schemes on ARM CPU in Raspberry
Pi. The authors of [72] developed a methodology for heterogeneously
quantized DNN models, targeting minimum energy consumption and high
accuracy with low latency. In a closely related work, the authors of [73]
presented a greedy search algorithm for solving the computationally hard
combinatorial optimization problem of selective layer quantization under
model-size constraints. A lightweight greedy algorithm works well under
the time constraints imposed by live accuracy feedback. However, the
greedy algorithm only explores a fraction of the exponential design space,
missing out on better solutions.

5.3

implementation

We implement partially quantized DNN inference using ARM-CL, which
provides efficient primitives for DNN execution on ARM CPUs and
GPUs, making it particularly suited for ARM-based HMPSoCs such as the
RK3399Pro [74]. Initially, ARM-CL supported CPU- or GPU-only inference.
In Chapter 3, we extend it to enable mid-inference switching between CPU

76

piqi: partially quantized dnn inference on hmpsocs

Figure 5.5: Abstraction for CPU, GPU, and NPU integration implementation

and GPU layers. In Chapter 4, we further enhance it with DVFS capabilities
to improve power efficiency. However, existing open-source frameworks
do not integrate NPU support or allow seamless switching between CPU,
GPU, and NPU mid-inference. To address this limitation, we develop ARM-
CO-UP, which integrates these features and is detailed in Chapter 7.

Figure 5.5 illustrates the ARM-CL-based implementation for PiQi . The
implementation takes as inputs the DNN model and the desired Run
Configuration, which specifies the partition of layers between CPU, GPU,
and NPU. In the case of the ARM big.LITTLE CPU, the CPU can be either a
big or LITTLE CPU for a given partition. It also describes the CPU and GPU
layer-level DVFS settings. NPUs do not support DVFS.

The Run Script in the implementation then prepares the NPU partitions
outside the ARM-CL context. It takes the Python model of the DNN and ex-
tracts out the parts marked for execution on NPU in the Run Configuration.
It then uses the vendor-specific NPU Tool, in the case of this work from
Rockchip, to quantize the NPU partitions. The NPU Tool tunes the partitions
for minimal quantization-related accuracy loss using sample images from
the training set. The partitions are now ready for use within ARM-CL.

The Run Script then invokes the ARM-CL context. ARM-CL converts
the DNN model into an internal multi-node C++ graph representation.
PiQi uses a Graph Creator to break the ARM-CL graph into N sub-graphs
for a Run Configuration with N component switches. Therefore, there is
one sub-graph for each contiguous single-component execution. PiQi adds
Receiver and Sender nodes to sub-graphs for the corresponding in and
out connections. PiQi uses an NPU Reconstructor to convert all nodes in

 WorkloadPrepare NPU PartsInitialize Sub-Graph CreatorDNN Pretrained ModelNPUCPUNPUGPU Graph Manager Graph Execution Workload Workload WorkloadSample ImagesInput, ReceiverFunctionsOutput, SenderInput, ReceiverFunctionsOutput, SenderInput, ReceiverFunctionsOutput, SenderInput, ReceiverFunctionsOutput, SenderNPUCPUNPUGPURunConfigurationNPU Model PreparerPython Modules andNPU ToolsNPU Partition 1NPU Partition mQuantized andconverted NPUPartitionsSetupDNN Model ARM-CL FormatRun1234InputsARM-CL Context5.4 characterization

77

]
t
t
a
W
/
S
P
F
[

y
c
n
e
i
c
fi
f
E
r
e
w
o
P

3.1

3

2.9

2.8

·10−2

1

Power Efficiency Gains

Accuracy [%]

68.8

68.6

68.4

]

%

[

y
c
a
r
u
c
c
A

75

Quantized Layer ID

Figure 5.6: Power efficiency and accuracy for the full design space in one-layer

quantization for Yolov3.

an NPU sub-graph, except the Receiver and Sender nodes, into a single
NPU node. PiQi then replaces this NPU node with the corresponding quan-
tized (and tuned) NPU partition prepared earlier. The NPU uses a Graph
Manager to connect the sub-graphs. Finally, PiQi uses a Graph Executor to
execute the connected sub-graphs. PiQi also applies layer-level CPU and
GPU DVFS using the Graph Executor, as per the Run Configuration.

This implementation, which enables running the model on HMPSoC
processors with a desired configuration, forms an essential operational
component of PiQi . In contrast, the optimization process in PiQi, detailed
in Section 5.5, utilizes the GA algorithm and prediction models for accuracy,
power, and performance. It aims to identify the optimal configuration that
achieves the target accuracy.

5.4 characterization

Partially quantized inference with PiQi inherently involves executing some
layers of the DNN on the NPU with quantization while executing other lay-
ers on a CPU or GPU with full precision. We perform a power-performance
and accuracy loss characterization for partially quantized DNN inference.
We use YoLov3 as an example DNN for this characterization because of
its large and complex neural architecture. Nevertheless, we make similar
observations for MobileNet. There are (cid:0)N
(cid:1) design options for selecting X
out of N DNN layers for quantization with PiQi. YoLov3 comprises of 75
partitionable layers. Figure 5.6 shows the impact of executing a single layer
(i.e., (cid:0)75
(cid:1) different design points) on the NPU with quantization and the
remaining layers executing at full precision on the big CPU running at full
frequency. Figure 5.6 shows the entropy in power efficiency and accuracy
with one-layer quantization.

X

1

78

piqi: partially quantized dnn inference on hmpsocs

Two-Layer Quantization Better One-Layer Quantization Better

·10−2
3

2.8

]
t
t
a
W
/
S
P
F
[

.
f
f
E
r
e
w
o
P

60

40

20

2nd Layer

20

40

60

1st Layer

(a) Efficiency

y
c
a
r
u
c
c
A

68.5

68

20

40

60

1st Layer

(b) Accuracy

60

40

20
2nd Layer

Figure 5.7: Power efficiency and accuracy for the down-sampled design space in

two-layer quantization for Yolov3.

These power, performance, and accuracy behaviours exhibit even higher
entropy when multiple layers in a DNN are quantized together, as shown
in Figure 5.7. Figure 5.7 (a) and Figure 5.7 (b) show the power efficiency
and accuracy of (cid:0)75
(cid:1) design points in two-layer quantization for YoLov3,
respectively. Let tuple (A, B) represent the simultaneous quantization of
layers A and B of the DNN. Intuition dictates power efficiency and accuracy
of two-layer quantization (A, B) versus either single-layer quantization (A)
or (B) should be higher and lower, respectively.

2

Figure 5.7 (a) compares the power efficiency of (A, B) with (A) and
(B) for YoLov3. The figure shows the power efficiency of the two-layer
quantization design point is better in most cases. In some cases where
either of the one-layer quantization design points is better, we trace them to
power-efficiency loss from the additional component switching overhead in
the quantizing two non-contiguous layers dominating the power efficiency
gains of additional quantization. Figure 5.7 (b) compares the accuracy
of (A, B) with (A) and (B) for YoLov3. The figure shows that two-layer
quantization can lead to higher or lower accuracy loss. This observation
stems from the fact that error propagation through a DNN architecture is
not well understood. It is possible for the errors from two quantized layers
to cancel out partially.

5.5

piqi framework

We introduce the PiQi framework for the partial quantization of DNNs on
HMPSoCs. PiQi consists of modelling and optimization parts, as shown in
Figure 5.8. The modelling part creates power, performance, and accuracy
models for a user-specified DNN model. The optimization part finds the

5.5 piqi framework

79

Figure 5.8: Abstraction showing the functioning for the proposed PiQi framework.

power-performance Pareto-front (using the models) for a user-defined accu-
racy constraint. Using prediction models instead of live data allows several
magnitudes faster evaluation of a partially quantized DNN configuration.

Modelling. The modelling part of PiQi operates first by taking the user-
specified DNN model as an input. A layer in the DNN can be either
quantized or non-quantized. Therefore, 2N possible partially quantized
configurations (design points) are possible for a DNN with N layers. The de-
sign space is even larger as every non-quantized layer in the configuration
can execute with full precision on a CPU or GPU at different DVFS levels.
The quantization of a layer within the DNN often leads to the loss of certain
feature information. This information loss propagates through the DNN,
influencing subsequent computations to the last output layer and thus
introducing errors in the prediction accuracy of the DNN. Determining the
cumulative impact of information loss on prediction accuracy from multiple
layers is non-trivial as the processed data undergoes multiple activation
and soft-max functions before reaching the final output. Consequently, an
analytical model for accuracy loss under partial quantization is hard to
design. Therefore, we use a ML model to predict the accuracy.

Since training with the entire design space is not feasible, PiQi uses
a sample generator to create a list of sample configurations across the
space. It uses all design points from 1- and 2-layer quantization, whereas
it uses Monte Carlo sampling for 3-layer quantization and beyond. It then
evaluates the accuracy of all of these configurations using a HPC server,
taking 5 minutes on average to assess a configuration accuracy.

PiQi uses the accuracy data from sample configurations to train a dense
neural network, as depicted in Figure 5.8, for predicting accuracy loss. The
model comprises three fully connected layers with 128, 64, and 8 neurons,
respectively, spanning from the input to the output layer. The model’s

Target DNNModelTarget DNNModelPartiallyQuantizedSamplesMap OnProcessorsHigh PerformanceServer [COCO Dataset]Rock Pi EmbeddedHMPSoCConnected To APower SetupPerformance/PowerDatabaseAccuracyDatasetNSGA-IIInitializationPopulationFitnessNon-DominatedSortSelectionAccuracy PredictorNN ModelPerformanceModelPower ModelFinalPopulationFilterAccuracyPerformanceand PowerMeasuremetnFinalResultsAccuracy ModelingPerformance/Power ModelingModelingOptimizationModels80

piqi: partially quantized dnn inference on hmpsocs

input is a binarized vector of size N, where each element is either 0 or 1,
representing a non-quantized or quantized layer, respectively. PiQi tailors
the accuracy predictor model for each DNN intended for deployment on
the HMPSoC with an NPU using independent training. We train Yolov3 and
MobileNet models separately in this work with 18331 and 4689 data samples,
respectively. It takes the server 5 minutes on average to train the model.

PiQi also predicts the power consumption and performance of a configu-
ration. In Chapter 4, we provide an analytical power-performance model for
mid-inference switching between CPU and GPU. The model also accounts
for the overhead of component switching and CPU/GPU DVFS. We extend
their model to account for overhead for back-and-forth switching with the
NPU. The analytical model requires a power-performance profile for every
layer on each component to work. We use an Arduino-based setup to directly
profile layers on the CPU and GPU on the HMPSoC. However, in the case
of the NPU, all layers are simultaneously loaded into an opaque vendor-
specific NPU context. This context does not make it transparent when one
layer ends and the other starts, making it infeasible for our profiling setup
to attribute the power and performance to individual layers. Therefore, we
use hybrid CPU-NPU configurations to profile an individual layer on the
NPU while excluding the impact of data transfer and loading times. It takes
the profiling setup 10 minutes on average to create a power-performance
profile for a configuration. Most profiling time overhead originates from
the one-time setup cost of loading the DNN model to the NPU and not
from actual inference.

Optimization. The optimization part of PiQi follows the modelling part
and takes in the user-defined accuracy constraint as input. PiQi uses a
multi-objective GA to determine the power-performance Pareto front under
accuracy constraints for partially quantized DNN inference. PiQi performs
a one-time encoding of configurations into chromosomes for the GA. The
GA starts with randomly selected configurations as the initial population.
It then uses the power, performance, and accuracy models to evaluate the
fitness of configurations in the population. It takes less than a millisecond
on average to evaluate the fitness of a configuration. A configuration in
the population is unfit if it violates the accuracy constraint or is Pareto-
dominated by another configuration in the population in terms of power
and performance. The GA eliminates the unfit part of the population and
uses mating functions (crossover and mutation) to produce new offspring
from the surviving configurations as replacements. The process iterates till
the GA fails to produce stronger offsprings.

5.6 evaluation

81

Table 5.1: The model-based prediction accuracy within PiQi .

YoLov3

MobileNet

Samples

MAE

Avg.

Samples

Metric

Power

Perf.

Acc.

MAE
96 mW[1.7%]
634 ms[9.8%]
0.0654%

Avg.
5636 mW
6602 ms
68.0833%

300

300

2732

226 mW[5.3%] 4217 mW 1000
1000

236 ms

9 ms[3.8%]
0.0258%

67.9117%

809

PiQi uses the NSGA-II algorithm [75] for the multi-objective GA. It
runs on the server and converges to a solution on average in around one
hour. Finally, the power-performance Pareto-front solution from the GA is
adjusted based on real power, performance, and accuracy measurements to
compensate for modelling errors before delivering the final results.

5.6

evaluation

We evaluate PiQi using the Rock-Pi N10 embedded platform containing
an RK3399Pro HMPSoC, shown in Figure 5.1. Considering end-to-end
latency and overall HMPSoC power consumption, our reported results
encompass all overheads, including processor switching, quantization and
dequantization during NPU transitions, data transfer, and synchronization.
We use two DNNs, MobileNet and YoLov3, that show significant enough
accuracy loss with quantization (Figure 5.3) yet are also compatible with
our extended ARM-CL implementation (Figure 5.5). ARM-CL integrates
several models like AlexNet and GoogleNet in Caffe format incompatible with
our partial quantization implementation. We use 50,000 and 5,000 images
from the ImageNet and COCO datasets to evaluate the image classification
and detection accuracy for MobileNet and YoLov3, respectively. We use Keras
API for TensorFlow to train the accuracy models.

Prediction Results. Table 5.1 provides the prediction errors, measured
as MAE, for power, performance, and accuracy models used within PiQi,
demonstrating high modeling precision. The low error (MAE = 0.0654% for
YOLOv3 and 0.0258% for MobileNet) of the accuracy prediction model, can
be attributed to the narrow variability in accuracy ranges observed across
models (approximately 4% for YoLov3 and 1% for MobileNet).

Baseline. No existing work proposes partially quantized DNN inference
on HMPSoCs. Therefore, we choose a recent greedy algorithm from [73]
that solves a similar combinatorial optimization problem of selective layer
quantization as PiQi as a baseline. The original greedy algorithm proposed

82

piqi: partially quantized dnn inference on hmpsocs

Table 5.2: MobileNet layer mappings for different accuracy.

Accuracy

Sample Layer Mapping

Num. Quantized Layers Best Time

Best Power

68.36
68.36
68.25
68.15
67.34

LLLLLLLLLLLLLL

GLLLLLLNNNBNNN

GLLLLNNNNNNNNN

GGNNNNNNNNNNNN

NNNNNNNNNNNNNN

0

6

9

12

14

[Overhead%]
137 ms [0%]
100 ms [9%]
77 ms [10%]
63 ms [20%]
29 ms [0%]

3404 mW
3229 mW
3207 mW
3158 mW
3108 mW

in [73] is a single-objective optimization algorithm that provides a trade-off
between accuracy and model size. We adapt the algorithm to select layers
for quantization under an accuracy constraint and call the adaption GSA,
short for greedy search algorithm. GSA initializes by marking all layers for
full-precision inference. It then greedily marks the layer expected to cause
the minimum accuracy loss for quantization. It repeats the greedy marking
process iteratively until further marking violates the accuracy constraint.
The iteration ends with a valid design point wherein GSA marks each layer
for full-precision or quantized execution. GSA then executes the design
point on all full-precision components (CPUs or GPU) at all DVFS levels
to get the Power-Performance Pareto-frontier.

Optimization Results. Table 5.2 presents sample configurations detailing
the layer mappings to NPU (N), GPU (G), big (B), and LITTLE (L) CPU
clusters alongside the maximum number of quantized layers for each
target accuracy in MobileNet. It also showcases the latency and power
consumption achieved among the Pareto-front results of PiQi for each
target accuracy. Remarkably, even at the first target accuracy (68.36%),
corresponding to the accuracy of the full precision model (first row),
quantizing six selective layers (second row) leads to improvements in both
time and power consumption. For a trade-off of only 0.21% accuracy (target
accuracy=68.15), quantizing 12 out of 14 layers is feasible. Notably, while a
fully quantized model would entail an accuracy drop to 67.34%, selectively
quantizing layers allows for enhanced power and latency performance with
minimal accuracy compromise.

Overhead. The Best time column in Table 5.2 includes the overhead
shown in brackets, representing the percentage of time spent on switching
processors and transferring data. The main overhead contributes to convert-
ing and loading to the NPU processor. As the output of the initial layers
is larger, switching to NPU at earlier layers introduces more overheads.

5.6 evaluation

83

GPU

big CPU

LITTLE CPU

GSA

PiQi

e
m
u
l
o
V
r
e
p
y
H

.

m
r
o
N

1.8

1.6

1.4

1.2

1

67.5

68

Accuracy [%]

(a) MobileNet

e
m
u
l
o
V
r
e
p
y
H

.

m
r
o
N

2

1.5

1

66

68

Accuracy [%]

(b) Yolov3

Figure 5.9: Power-Performance Pareto-front hyper volume comparison.

For example, one switch to the NPU from the second layer introduces
high overhead for the 68.15% accuracy target case, while for the second
row (target accuracy=68.36%), switching to the NPU happens at latter
layers, which induces relatively less overhead (9% overhead for 4 switches).
Comparative Results. We evaluate GSA and PiQi for YOLOv3 and Mo-
bileNet DNNs under different accuracy constraints within their achievable
accuracy ranges. For each DNN, the accuracy constraints are bounded by
the quantized- and full-precision-only inference accuracy. Both GSA and
PiQi use the same prediction model from Section 5.4 for fairness.

For each target accuracy, we compare the multi-objective optimizations
(power and latency Pareto-front) of the two methods using normalized
hyper-volume as the metric. A fixed reference point is established for each
DNN by selecting the maximum power consumption and latency among
Pareto front design points of single components. The reference points are
(20320 ms, 7200 mW) for YOLOv3 and (550 ms, 7000 mW) for MobileNet.

Figure 5.9 reports the model-based normalized hypervolume of the
power-performance frontier obtained using the two methods for the se-
lected accuracy constraints. While the Pareto frontier results of single-
component inference remain fixed for different target accuracies, the power-
latency Pareto frontier of PiQi consistently improves with decreasing target
accuracy due to increased layer quantization. However, it’s crucial to ac-
knowledge that this improvement isn’t consistent across all scenarios for
GSA. In some intervals, particularly within GSA, where extensive switching
occurs, there may be instances where the power-latency performance does
not improve and may even degrade due to the overhead incurred from
switching between processors and quantization/dequantization processes.
The power-performance Pareto frontier provided by PiQi always dominates
the frontier from GSA. Figure 5.9 (a) and Figure 5.9 (b) show PiQi providing,

84

piqi: partially quantized dnn inference on hmpsocs

on average, 11.6% and 18.1% higher hypervolume than GSA (with the
mentioned reference points) for MobileNet and YoLov3, respectively.

5.7

summary

This chapter introduced PiQi, a framework for partially quantized DNN
inference on HMPSoCs, addressing the challenge of integrating NPUs
alongside CPUs and GPUs while maintaining accuracy requirements. We
demonstrated that different DNN layers exhibit varying sensitivity to quan-
tization, with some tolerating lower precision, while others suffer signifi-
cant accuracy loss. NPUs offer superior power and performance efficiency,
but their reliance on quantization can make them unsuitable for accuracy-
sensitive applications. PiQi leverages this layer-wise variability, dynamically
assigning layers to CPU, GPU, or NPU to balance accuracy, power, and
performance. By selectively executing certain layers in full precision on
CPUs/GPUs while running others in quantized mode on the NPU, PiQi
ensures that accuracy constraints are met without sacrificing efficiency.

PiQi provides a low-overhead implementation for mid-inference switch-
ing across processors, enabling seamless execution across heterogeneous
architectures. Additionally, it integrates a neural network-based accuracy
prediction model, which expedites the search process, making it feasible
to explore the large design space of layer quantization, processor mapping,
and DVFS configurations. By combining this with a multi-objective GA,
PiQi efficiently identifies Pareto-optimal solutions that maximize power
and performance efficiency while meeting accuracy constraints. Empirical
evaluations on the Rock-Pi N10 (RK3399Pro HMPSoC) demonstrate that
PiQi significantly outperforms state-of-the-art, achieving a superior power-
performance Pareto frontier for constrained accuracy scenarios.

While the focus so far has been on latency, power efficiency, and accuracy,
many real-time applications require not only low-latency inference but also
high throughput. The next chapter shifts focus from latency optimization
to throughput-aware execution, exploring how parallel and pipeline-based
execution strategies across CPUs, GPUs, and NPUs can further enhance
efficiency in modern HMPSoCs.

6

I N T E G R AT E D P I P E L I N E F O R
H I G H - T H R O U G H P U T C N N
I N F E R E N C E

In the previous chapters, we primarily focused on optimizing inference
latency by dynamically switching execution among available proces-
sors—initially between CPU and GPU, and later incorporating the NPU.
These approaches relied on serial execution strategies, where only one
processing unit was active at a time to improve inference efficiency by
running each part of the model on the most suitable processor for that part
to achieve the best overall performance.

In this chapter, we shift focus from latency to high-throughput infer-
ence, exploring pipeline-based execution, which enables parallel processing
across multiple heterogeneous processors. Instead of dynamically switch-
ing execution between processing units, we introduce layer-level pipelin-
ing, allowing different CNN layers to execute concurrently on separate
processors. This approach is crucial for real-time applications that require
high FPS since failing to maintain the required FPS can lead to buffering,
queuing delays, and even latency spikes that degrade responsiveness. By
fully utilizing all available processing units in parallel, pipeline-based
inference mitigates these issues while enhancing efficiency.

This chapter introduces a three-stage Pipe-ALL framework that leverages
the big CPU cluster, LITTLE CPU cluster, and GPU to enable concurrent exe-
cution of different CNN layers. We systematically explore layer-to-processor
mappings, identifying optimal configurations that maximize throughput
compared to single-processor inference. By effectively distributing compu-
tation across heterogeneous processors, this approach improves resource
utilization and enhances system performance.

Building upon this, we extend the pipeline in two key ways: first, by
integrating the NPU to further enhance inference performance, and second,

85

86

integrated pipeline for high-throughput cnn inference

by optimizing not only throughput but also energy efficiency. Additionally,
to achieve energy efficiency, we incorporate per-stage DVFS adjustments, al-
lowing fine-grained control over power consumption. These advancements
introduce new design challenges, as CPU-GPU-NPU pipelining and energy-
aware optimization significantly expand the search space. To systematically
explore this space, we employ a GA-based optimization framework, which
efficiently navigates layer assignments, DVFS configurations, and processor
choices to maximize throughput while minimizing energy consumption.

This Chapter is based on:

• E. Aghapour, Y. Zhang, A. Pathania, T. Mitra "Pipelined CNN Inference
on Heterogeneous Multi-processor System-on-Chip" [76], in Embedded Machine
Learning for Cyber-Physical, IoT, and Edge Computing: Software Optimizations
and Hardware/Software Codesign, 2023 © Springer.

• E. Aghapour, A. Pathania, G. Ananthanarayanan "Integrated ARM big.
LITTLE-Mali pipeline for high-throughput CNN inference" [77], in Authorea
Preprints, 2023

• E. Aghapour, Y. Shen, D. Sapra, A. Pimentel, A. Pathania "ARM-CO-UP:
ARM CO operative U tilization of P rocessors" [64], in ACM Transactions on
Design Automation of Electronic Systems, 2024

6.1

introduction

In real-time applications, maintaining low latency is critical to ensur-
ing timely responses. However, for many high-performance applications
throughput is equally, if not more, important. A system that meets strict
latency constraints but fails to sustain high FPS throughput may suffer
from queuing delays, buffering, and inconsistent performance. This makes
throughput a key optimization target, particularly for workloads that re-
quire continuous processing of high-volume data streams.

To improve inference throughput, this chapter first focuses on the two
most commonly available processors in embedded platforms: CPU clusters
and GPU. These processors are widely supported by software frameworks,
making them practical choices for pipeline-based inference. Figure 6.1
presents the stand-alone inference throughput of the CPU clusters and GPU
on the Khadas Vim 3 platform. The results indicate that depending on the
network architecture, either the big CPU or the GPU can provide the highest

6.1 introduction

87

LITTLE CPU Cluster

big CPU Cluster GPU

]
S
P
F
[

t
u
p
h
g
u
o
r
h
T

20

10

0

AlexNet

GoogleNet

MobileNet

ResNet50

SqueezeNet

Figure 6.1: The inference throughput for different inference capable components

for different CNNs on Khadas Vim 3.

single-component performance, while the LITTLE CPU contributes modest
but notable throughput. However, the overall performance remains limited,
with none of the benchmarks reaching the recommended 30 FPS for a basic
user experience [78]. Consequently, leveraging both CPU clusters and the
GPU simultaneously is essential in end devices.

A strategy for enhancing inference throughput is multi-component ex-
layers, yet direct multi-
ecution. CNNs consist of multiple sequential
component inference—wherein a single layer is processed simultaneously
on different CPU clusters—can degrade performance [29]. This perfor-
mance drop is attributed to increased memory traffic required for main-
taining cache coherence. Additionally, no framework supports executing a
single CNN layer concurrently on both CPU and GPU.

One of the most effective approaches for multi-component inference is a
pipeline-based design that operates at layer-level granularity. In this design,
each inference-capable component functions as a pipeline stage, allowing
multiple frames to be processed simultaneously. For instance, while one
stage processes layers from Frame N, another stage processes layers from
Frame N+1. To minimize interconnect traffic, consecutive CNN layers are
assigned to the same pipeline stage whenever possible, as each layer’s
output typically serves as the next layer’s input.

HMPSoCs with integrated CPUs and GPUs (which are common pro-
cessors in end devices) are well-suited for inference pipeline designs, as
both processing units can operate under a unified execution framework.
In this work, we utilize ARM-CL to construct a three-stage inference
pipeline—Pipe-ALL—incorporating the big CPU, LITTLE CPU, and GPU.
Beyond Pipe-ALL, integrating NPUs presents an opportunity for further
performance improvements. However, unlike CPUs and GPUs, NPUs lack
standardized execution frameworks and rely on vendor-specific, propri-
etary solutions, making their integration into a unified inference pipeline
challenging. Existing pipeline designs do not incorporate NPUs, and their

88

integrated pipeline for high-throughput cnn inference

LITTLE

big GPU NPU

]
S
P
F
[

t
u
p
h
g
u
o
r
h
T

15

10

5

0

AlexNet

GoogleNet

MobileNet

ResNet50

SqueezeNet

Figure 6.2: Minimum and maximum throughput of different HMPSoC compo-

nents with different CNNs

LITTLE

big GPU NPU

]

W
m

[
n
o
i
t
p
m
u
s
n
o
c

r
e
w
o
P

6,000

4,000

2,000

0

AlexNet

GoogleNet

MobileNet

ResNet50

SqueezeNet

Figure 6.3: Minimum and maximum power consumption of different HMPSoC

components with different CNNs

potential benefits for non-quantized inference remain underexplored. In the
second part of this chapter, we propose a CPU-GPU-NPU pipeline on the
Rock Pi platform, where the NPU supports non-quantized models.

While improving inference throughput is a primary goal, energy ef-
ficiency remains a key consideration. The DVFS settings of processors
significantly impact both performance and power consumption. Figure 6.2
illustrates how inference throughput varies with DVFS settings for different
processing units. Notably, the NPU lacks independent DVFS control and
relies on the host CPU’s configuration, particularly the big CPU. Figure 6.3
further shows that increasing frequency enhances throughput at the cost of
higher power consumption.

Optimizing a CPU-GPU-NPU pipeline for high throughput and energy
efficiency requires careful layer partitioning, processing unit selection, and
DVFS tuning. In subsequent sections, we explore the design space and

6.2 related work

89

methodologies for optimizing pipeline configurations to enhance both
throughput and energy efficiency.

Novel Contributions: This work makes the following key contributions:

• We present the first implementation of a tightly integrated three-stage
CPU-GPU pipelining framework, Pipe-ALL, leveraging ARM-CL for
CNN inference on ARM big.LITTLE CPUs and Mali GPUs.

• We extend the Pipe-ALL by integrating an NPU, enabling a heteroge-

neous inference pipeline.

• We incorporate a DVFS mechanism into the integrated CPU-GPU-
NPU pipeline and conduct a comprehensive design space analysis.

• We introduce a multi-objective optimization approach to maximize
throughput and power efficiency by optimizing model partitioning,
processor mapping, and DVFS settings.

• We implement and evaluate Pipe-ALL on the Amlogic A311D HMPSoC
within the Khadas Vim 3 platform, achieving an average through-
put improvement of 75.88% over peak single-component inference
throughput.

• We validate our GA optimization for the CPU-GPU-NPU pipeline
with DVFS on the Rockchip RK3399 HMPSoC within the Rock Pi
N10 platform, achieving maximum throughput and energy-efficient
inference without accuracy loss.

Open Source Contributions: The implementation of Pipe-ALL is pub-
licly available at https://github.com/Ehsan-aghapour/ARMCL-Pipe-All under
the MIT license.

6.2 related work

Multi-component inference through pipelining is an active area of research.
The authors of [29] were the first to create a layer-level inference pipeline
between big and LITTLE CPU clusters in an ARM big.LITTLE asymmetric
multi-core processor to improve CPU inference throughput. Their work also
employs ARM-CL. However, their pipeline design relies on migrating CPU
threads between big and LITTLE cores, which cannot be extended to include
a GPU, as CPU threads cannot be migrated to a GPU. The authors of [79,
80] propose to optimize inference pipelines on asymmetric multi-cores.

90

integrated pipeline for high-throughput cnn inference

Recently, several studies [37, 81, 82] have explored CPU-GPU synergy to
improve CNN inference throughput on embedded platforms with Nvidia
GPUs using the TensorRT framework. These approaches primarily use the
GPU as an accelerator to offload computations from a CPU-only pipeline
design. However, the CPUs in these studies are of symmetric design. These
designs present a potential alternative to our pipeline approach, though di-
rect comparison is difficult due to differences in platforms and frameworks.
Furthermore, none of the above works have made their design open-source.
The authors of [27] propose a Parallel execution strategy that allows
multiple processing units to perform independent inference simultane-
ously. This method utilizes all available hardware resources to maximize
throughput but does not coordinate execution across components. As a
result, the overall inference latency is determined by the slowest processing
unit, leading to suboptimal worst-case performance. In our evaluation, we
compare our Pipe-ALL against this Parallel method to highlight the benefits
of a coordinated execution strategy. Unlike[27], which runs inference inde-
pendently on each component, our approach strategically assigns layers to
pipeline stages to balance computation across heterogeneous processors,
enhancing throughput while controlling latency rather than relying on
purely independent execution.

While utilizing NPUs alongside CPUs and GPUs in SoCs, many recent
research efforts [27, 38, 43, 82–84] have explored power, energy, and perfor-
mance trade-offs, aiming to identify optimal design points in this extended
space. MOSAIC [38] introduces CNN model partitioning techniques that
distribute model shards across CPU, GPU, and NPU components, consid-
ering their heterogeneous power-performance efficiencies and communi-
cation overhead. However, this work does not parallelize CNN execution
across these processing units.

To maximize throughput, the authors of [82, 83] propose a TensorRT-
based framework that pipelines inference at the layer level using GPUs
and NPUs while employing multi-stream execution to enhance parallelism.
However, their approach excludes CPU clusters, despite modern end de-
vices demonstrating comparable deep learning performance on CPUs and
GPUs. Furthermore, they do not explore energy-performance trade-offs via
voltage and frequency scaling of GPU and CPU processors. The number of
pipeline stages and mapping options are also manually determined.

AxoNN [84] enables energy-performance trade-offs by distributing NN
layers between performance- and power-efficient accelerators (GPU and
NPU). The work most closely related to ours is [43], which employs

6.3 pipeline execution

91

a genetic algorithm to map DNN layers onto heterogeneous processors
under various objective functions. While they consider NPUs as possible
processing elements, no experiments have been conducted with NPUs.
Additionally, CPU and GPU utilization follow the default DVFS policy,
without voltage and frequency adjustments to optimize design points.

In contrast to the above works, we are the first to introduce an open-
source integrated three-stage pipeline design, Pipe-ALL, with the big CPU,
LITTLE CPU, and GPU as its stages. Furthermore, none of the above work
explores the performance-energy design space by combining pipelined
inference with DVFS.

6.3

pipeline execution

ARM-CL optimizes CNN inference for ARM-based HMPSoCs but is in-
herently limited to executing on a single processor at a time. It does not
support parallel (pipeline) execution across multiple processing units, such
as the big CPU cluster, LITTLE CPU cluster, and GPU. We extend ARM-CL
into Pipe-ALL framework to distributed CNN inference across HMPSoC
processors in a pipelined manner. This is achieved by partitioning the
CNN computation graph into subgraphs, where each subgraph executes
on a different processor. We introduce synchronization mechanisms, data
transfer nodes, and buffering techniques, allowing different parts of a
model to run efficiently in parallel.

Pipe-ALL enables partitioning a CNN and executing different parts on the
LITTLE CPU, big CPU cluster, and GPU based on predefined partitioning
points and processor mappings. While this setup supports pipeline execu-
tion across heterogeneous processors, it does not inherently balance the
workload across them. Instead, it establishes the necessary infrastructure
for synchronized execution, where Transfer and Receiver nodes manage
data movement, and buffer tensors facilitate efficient inter-processor com-
munication. The effectiveness of this workload distribution depends on how
the CNN is partitioned and mapped, which is explored in the next section
through design exploration and optimization strategies. A detailed expla-
nation of how Pipe-ALL implements pipeline execution within ARM-CL,
including synchronization, buffering, and workload distribution strategies,
is provided in Chapter 7.

Moreover, we further extend Pipe-ALL to a CPU-GPU-NPU pipeline,
incorporating the NPU to enhance throughput. However, integrating the
NPU into a unified inference pipeline introduces several technical chal-

92

integrated pipeline for high-throughput cnn inference

Pipe-ALL Stage 1

Pipe-ALL Stage 2

Pipe-ALL Stage 3

Frame

N+4

Sub-Graph1
Processing
Frame N+3

Sub-Graph2
Processing
Frame N+2

Buffer 1

Sub-Graph3
Processing
Frame N+1

Frame

N

Buffer 0

Figure 6.4: An abstraction showing high-throughput (low-latency) pipelined infer-

encing of a stream on a HMPSoC using CPU-GPU pipeline design.

lenges. The detailed design and implementation of this integration are
presented in Chapter 7. The CPU-GPU-NPU pipeline automatically parti-
tions the pre-trained model, converts and prepares the NPU segments, and
synchronizes NPU execution with CPU-GPU processing in a synergistic
pipeline. Optimizing throughput in this CPU-GPU-NPU pipeline requires
careful model partitioning and efficient processor mapping. Additionally,
tuning DVFS settings for each processor can further enhance throughput
and energy efficiency.

6.4 methodology

In this section, we first analyze the design space for Pipe-ALL, focusing on
model partitioning and processor mapping. We then present the method-
ology for identifying the optimal design point within this space. Next,
we extend this analysis by integrating the NPU and DVFS, expanding
the design space to include model partitioning, processor selection, and
DVFS configurations for each processing unit. Finally, we introduce the
optimization method used to efficiently explore this extended design space.

6.4.1 Pipe-ALL Framework

Pipe-ALL framework proposed in this work processes three separate frames
simultaneously on big CPU, LITTLE CPU, and GPU, as shown in Figure 6.4
with an abstract block diagram. However, it doesn’t process these frames
in their entirety in any component. The pipeline allows us to distribute
the processing of a given frame between the three components at node-
level (near layer-level) granularity. The processing distribution between
the components inversely correlates to their inference capabilities for the
given CNN. For example, the LITTLE CPU cluster always receives the

6.4 methodology

93

Graph

Layers

Partition Points

Design Space

Search Time

AlexNet

GoogleNet

MobileNet

ResNet50

SqueezeNet

11

58

28

54

26

7

12

27

17

18

126

396

2106

816

918

2 Hours

5 Hours

11 Hours

8 Hours

7 Hours

Table 6.1: The design space parameters for different CNNs under Pipe-All.

least processing load for a frame as it is the weakest inference-capable
component in the HMPSoC for all CNNs. Nevertheless, this distribution
allows all the frames processed on HMPSoC with Pipe-ALL to have the
same latency, to prevent a pipelining botteneck.

Design Space: Since the number of stages in Pipe-ALL is only three and
the processing distribution between the stages must maintain the sequential
layer-wise processing order, its design space is small. Table 6.1 shows the
number of layers and number of partition points in different CNNs. The
number of partition points is less than the number of layers because non-
convolution layers (except fully-connected layers) do not have a Main node
associated with them in the ARM-CL graph and are therefore not viable
partition points. Furthermore, within Pipe-ALL, all Main nodes that can
be processed independently are grouped into a single partition point and
processed simultaneously to maximize throughput.

A CNN with N partitions has N − 1 partition points. To form a three-
stage pipeline, we select two partition points, ensuring no empty stages.
The first split at position i leaves (N − 1) − i choices for the second split.
Summing over all i gives:

(N − 1)(N − 2)
2

(1)

With three stages mapped to LITTLE, big, or GPU, there are 3! = 6

assignments. Thus, the total pipeline configurations under Pipe-ALL are:

3(N − 1)(N − 2)

(2)

Optimization: Since the CNN inference workload is static, these con-
figurations can be reliably profiled at design time to quickly determine
throughput. Even for MobileNet, which has the highest number of config-
urations (2106) among all CNNs, this profiling takes only 11 hours on the

94

integrated pipeline for high-throughput cnn inference

Khadas Vim3 embedded platform. Thus, we obtain the optimal configura-
tion (maximizing throughput) for each CNN through exhaustive search.
Table 6.1 presents the number of configurations and the corresponding
search time for different CNNs on the Khadas Vim3 platform.

6.4.2 CPU-GPU-NPU Pipeline with DVFS

In designing a more extensive pipeline for inference across heterogeneous
processors—including an NPU, a GPU, big CPU, and LITTLE CPU—we
assume that each processor, if used, is assigned a single contiguous block
of layers. This arrangement minimizes inter-processor communication over-
head by transferring intermediate results only at block boundaries while
allowing the system to exploit pipeline parallelism effectively. Since not all
processors may be required, some can remain unused.

Design Space: Let N be the total number of layers and C the number
of available processors. Every valid assignment is obtained by selecting the
number of processors i to use (1 ⩽ i ⩽ min(C, N)), partitioning the N layers
into i contiguous segments, and mapping those segments to the i chosen
processors. The total number of valid assignments (S) follows Equation (3).

min(C,N)(cid:88)

S =

i=1

(cid:18)C
i

(cid:19)(cid:18)N − 1
i − 1

(cid:19)

i!

Here,

(3)

i

• (cid:0)C
• (cid:0)N−1

(cid:1) accounts for selecting which i processors to use,

i−1

(cid:1) represents the number of ways to place i − 1 partition cuts
among the N − 1 gaps between consecutive layers, thereby dividing
the CNN into i stages.

• i! reflects the permutations of those i contiguous blocks among the i

chosen processors.

The number of possible assignments grows combinatorially with both the
number of layers N and the number of processors C. Even a modest increase
in N leads to an explosion in design possibilities. For instance, with 8 layers
and 4 processors, there are 1,432 valid assignments, whereas 20 layers (with
the same 4 processors) result in 27,592 distinct configurations. This growth
is approximated on the order of N(C−1) for fixed C, underscoring why
exhaustive search quickly becomes infeasible for larger DNNs.

6.4 methodology

95

Table 6.2: Design Space Configurations for Different CNNs

Graph

Partitioning DVFS Host Selection

Total Designs

AlexNet

GoogleNet

MobileNet

ResNet50

SqueezeNet

1432

7012

78,952

19,792

23,476

240

240

240

240

240

4

4

4

4

4

1,374,720

6,731,520

75,793,920

19,000,320

22,536,960

Additionally, optimizing energy consumption further expands the design
space. We incorporate DVFS settings for the GPU, big CPU, and LITTLE
CPU, where the voltage and frequency must be selected at setup time for
each processor cluster. However, the optimal DVFS configuration depends
on how the layers are mapped, while the best layer mapping itself can
depend on the DVFS settings. This interdependency dramatically increases
the number of possible configurations: for example, on a Rock Pi board, the
big CPU has 8 DVFS levels, the LITTLE CPU has 6, and the GPU has 5,
resulting in 240 possible DVFS configurations whenever these processors
are used. When these DVFS choices are combined with the already large
number of layer-to-processor mappings, the total design space becomes
enormous, and evaluating a single design point can take upto two minutes.
Moreover, the selection of the host processor for the GPU and NPU
further expands the design space. Each of these accelerators requires a
host processor to load input data, manage execution, and retrieve results.
The choice of host affects both the total performance and power consump-
tion of the workload running on the GPU/NPU, as well as the available
computational resources on the selected CPU cluster. One of its cores may
occasionally remain occupied managing execution for the GPU/NPU. For
each accelerator, there are two possible options for the host processor:
the big CPU or the LITTLE CPU. Consequently, this selection introduces
an additional four combinatorial choices, effectively increasing the design
space by a factor of four. Table 6.2 quantifies the total number of possible
design configurations across five different CNNs.

The combinatorial nature of this search space, combined with the interde-
pendence of layer assignment, DVFS selection, and host processor selection,
renders exhaustive search infeasible in a reasonable time. This necessitates
an efficient optimization strategy that can explore the space effectively

96

integrated pipeline for high-throughput cnn inference

Figure 6.5: Chromosome encoding scheme of GA for optimizing integrated CPU-

GPU-NPU pipeline configurations and DVFS settings.

while balancing multiple objectives, such as maximizing throughput and
minimizing energy consumption per inference.

Optimization: To efficiently explore this vast design space and optimize
the CPU-GPU-NPU pipeline, we employ a GA. GAs provide a structured
approach to navigating large combinatorial spaces by evolving candidate
solutions over multiple generations. They are particularly well-suited for
this problem because they:

• Require minimal prior modeling of the system,

• Efficiently explore the space using population-based search,

• Naturally accommodate both discrete (layer assignment) and contin-

uous (DVFS settings) variables.

While other methods such as reinforcement learning could be used to bal-
ance exploration and exploitation, they typically require extensive training
data and carefully structured reward functions. In contrast, GA requires
relatively less tuning and can converge on high-quality configurations
within a manageable evaluation budget.

To optimize the CPU-GPU-NPU pipeline design, we employ a GA-based
search strategy that effectively balances multi-objective trade-offs in this
large design space. Each candidate solution in the population represents
a specific pipeline configuration, including layer-to-processor assignments,
DVFS settings, and host processor selection.

The process begins with the creation of an initial random population P0,
where each individual encodes a unique combination of pipeline param-
eters. Each configuration is evaluated based on two key objectives: maxi-
mizing throughput and minimizing energy consumption. The population
is ranked using non-dominated sorting to identify Pareto-optimal solutions,
ensuring that configurations balancing these objectives are favored.

6.4 methodology

97

Chromosome Encoding and Representation

To efficiently explore the pipeline design space, each chromosome encodes
a unique configuration using the scheme illustrated in Figure 6.5. The
chromosome consists of four parts: DVFS settings, host selection, processors
order, and partitioning of the CNN.

• DVFS Settings: This part contains three genes corresponding to the
DVFS levels for the LITTLE CPU, big CPU, and GPU. Each gene
represents the DVFS level for its respective processor.

• Host Selection: This part encodes the host selection for both the GPU
and NPU. We map the four possible combinations of host selection
into a value between 0 and 3, requiring just one gene.

• Processors Order: This part determines the mapping of processors to
pipeline stages. It contains four genes, each specifying the processor
for a particular pipeline stage.

• Partitioning: This part defines how the CNN is partitioned into
pipeline stages. It contains four genes, where each gene specifies the
number of layers assigned to a particular stage. The sum of these
genes equals the total number of layers N.

With this encoding scheme, all possible configurations can be represented
as chromosomes, allowing for systematic exploration of the design space.
Each chromosome encodes a unique configuration, allowing it to be de-
coded and evaluated during the GA search process.

Selection, Crossover, and Mutation

Parents for the next generation are selected via binary tournament selection,
where candidates compete based on Pareto rank and diversity. They then
undergo crossover and mutation to generate an offspring population Qt,
exploring new regions of the design space while preserving valid pipeline
configurations. To ensure this, crossover and mutation must adhere to
specific constraints.

• In the processors order part, each processor must be used at most once.

• In the partitioning part, the sum of the genes must always equal N, the

total number of layers.

98

integrated pipeline for high-throughput cnn inference

To address these challenges, we refine the genetic mating operations as
follows:

• Crossover: Each of the four parts of a chromosome (DVFS, host
selection, order, partitioning) is treated as a separate module. During
crossover, these modules are swapped between two parent chro-
mosomes with a certain probability. This modular approach avoids
invalid configurations by preserving the integrity of each part and
allows for exploration across different dimensions of the design space.

• Mutation: Mutation explores within each dimension (DVFS, host

selection, order, or partitioning):

– For DVFS settings and host selection, the genes are randomly
altered, with the new values selected from a normal distribu-
tion centered around the current value. The standard deviation
decreases as the number of generations increases, balancing
exploration (larger changes early) and exploitation (smaller re-
finements later).

– For the order part, two randomly selected processors swap.

– For the partitioning part, two random pipeline stages are selected,
and a random k-value determines how many layers are shifted
from one stage to the other. Similar to DVFS, k is sampled
from a normal distribution with a decreasing standard deviation,
ensuring finer adjustments in later generations.

This refined approach ensures that all generated chromosomes remain
valid while maintaining diversity in the population. At each iteration t of
the GA, a new set of offspring Qt is generated by applying crossover and
mutation operators to the current population Pt. The offspring population
Qt is then combined with the parent population Pt to form Rt, which rep-
resents all explored configurations so far in that generation. This combined
population is ranked using non-dominated sorting, and the best solutions
go to the next generation Pt+1 based on rank and crowding distance, which
helps maintain solution diversity and prevents premature convergence.

Through this iterative process, the GA gradually refines the population,
guiding it toward improved solutions. Each generation introduces variation
through crossover and mutation while favoring configurations that enhance
throughput or energy efficiency. Over multiple iterations, the search space
is explored extensively in the early stages, followed by more fine-tuned

6.5 experimental evaluation

99

optimization as the algorithm progresses. This balance between broad
exploration and targeted exploitation ensures an effective search.

The process continues until a termination criterion is met, such as reach-
ing a predefined number of generations or convergence of the solutions. By
systematically evolving the population over iterations, the GA efficiently
navigates the large design space, avoiding local optima and converging
toward high-performing configurations.

6.5

experimental evaluation

Experimental setup. We evaluate the Pipe-ALL using the Amlogic A311D
HMPSoC on the Khadas Vim 3 embedded platform, as shown in Figure 2.3 in
Chapter 2. The HMPSoC features a hexa-core asymmetric ARM big.LITTLE
multi-core CPU with two clusters: a quad-core big cluster with four A73
cores and a dual-core LITTLE cluster with two A53 cores. Additionally, it
includes a dual-core Mali G52 MP4 GPU. The maximum operating frequen-
cies are 1.8 GHz for the big CPU cluster, 2.2 GHz for the LITTLE CPU cluster,
and 0.8 GHz for the GPU. Since the focus is solely on performance, all
processors operate at their maximum frequency. The platform is equipped
with 4 GB LPDDR4 main memory and runs Android v9.0 with kernel v4.9,
using ARM-CL v21.02 for inference execution.

For the CPU-GPU-NPU pipeline, we move to the RK3399Pro SoC on the
Rock Pi N10 embedded platform because its NPU supports non-quantized
inference, and both CPU clusters and the GPU support DVFS. This SoC
also features a hexa-core asymmetric ARM big.LITTLE CPU, but with a
different core distribution compared to the Amlogic A311D: a dual-core big
cluster with two A72 cores and a quad-core LITTLE cluster with four A53
cores. Additionally, it includes a quad-core ARM Mali-T860 MP4 GPU. The
LITTLE CPU cluster operates at six frequency and voltage levels ranging
from 408 MHz to 1416 MHz, while the big CPU cluster supports eight DVFS
settings from 408 MHz to 1800 MHz. The GPU operates under five DVFS
settings between 200 MHz and 800 MHz. The platform runs Android v8.1
with kernel v4.9, and the pipeline is built upon ARM-CL v21.02.

6.5.1 Pipe-ALL

We evaluate the Pipe-ALL based on two key metrics – throughput (measured
in FPS) and latency (measured in milliseconds). Ideally, the goal is to
maximize throughput while minimizing latency. We use two baselines to

100

integrated pipeline for high-throughput cnn inference

Peak

Parallel [27]

Pipe-All

]
S
P
F
[

t
u
p
h
g
u
o
r
h
T

]
s

m

[

y
c
n
e
t
a
L

60

40

20

0

1,000

500

0

AlexNet

GoogleNet

MobileNet

ResNet50

SqueezeNet

(a) Throughput

AlexNet

GoogleNet

MobileNet

ResNet50

SqueezeNet

(b) Latency

Figure 6.6: Results for different CNNs with different approaches.

evaluate the efficacy of the Pipe-ALL. The first baseline, symbolized by
Peak, represents the peak single-component inference performance, where
inference is executed on the most powerful individual processor available.
The second baseline, symbolized by Parallel, follows the approach proposed
by [27], where all HMPSoC components perform independent, simultane-
ous inference without a coordinated execution strategy.

Performance Evaluation: Figures 6.6 (a) and 6.6 (b) illustrate the through-
put and corresponding latency achieved using different techniques across
various CNNs. The Peak baseline results in low throughput since only the
highest-performing component is utilized, while other components remain
idle. However, it achieves very low latency, establishing an empirical lower
bound for the Pipe-ALL. In contrast, the Parallel baseline [27] achieves high
throughput by utilizing multiple components simultaneously, but its overall
latency is dictated by the slowest component, the LITTLE CPU cluster,
resulting in significantly higher worst-case latency.

Figure 6.6 shows that, on average, the Pipe-ALL provides 5.42% higher
throughput than the Parallel baseline and 75.88% higher throughput than
the Peak baseline. However, compared to the Peak baseline, this increase
in throughput comes at the cost of a 55.59% increase in latency, which
remains significantly lower than the 419.87% increase observed with the
Parallel baseline. These results highlight the efficiency of the pipelined de-

6.5 experimental evaluation

101

Little CPU big CPU GPU NPU (Non-Quantized)

Pipeline Mode

]
S
P
F
[

t
u
p
h
g
u
o
r
h
T

]
J

m

[

e
m
a
r
F

r
e
P
y
g
r
e
n
E

30

20

10

0

3,000

2,000

1,000

0

AlexNet

GoogleNet

MobileNet

ResNet50

SqueezeNet

(a) Throughput

AlexNet

GoogleNet

MobileNet

ResNet50

SqueezeNet

(b) Energy Consumption

Figure 6.7: Pipeline mode versus single-processor inference comparison.

sign within the Pipe-ALL, which effectively distributes computation across
components, balancing the latency of individual pipeline stages while
maintaining high throughput.

6.5.2 CPU-GPU-NPU Pipeline and DVFS

To evaluate the efficiency of the GA-optimized CPU-GPU-NPU pipeline
with DVFS, we assess its impact across multiple CNN models, focusing
on both throughput and energy efficiency. The pipeline’s inference results
are compared against standalone NPU execution, as the NPU is the most
power- and computation-efficient processor in the system.

Figure 6.7 presents the results across five CNN architectures, with sub-
figures 6.7 (a) and 6.7 (b) illustrating throughput and energy efficiency,
respectively, along with the contribution of each processor. The GA-based
framework efficiently explores the design space, identifying near-optimal
pipeline configurations despite the complexity of heterogeneous execution.
The optimized design significantly enhances both throughput and energy
efficiency, demonstrating the effectiveness of this approach.

Table 6.3 details the pipeline configuration for AlexNet, including layer-
to-processor mappings (L, B, G, and N representing LITTLE CPU, big CPU,

102

integrated pipeline for high-throughput cnn inference

Table 6.3: Extra-functional characteristics (inference time and energy per frame) of

AlexNet in Pipeline mode, focusing on layer mapping.

Layers Mapping

Host

Frequency (GHz)

Time (ms)

Energy (mJ)

GPU NPU

LITTLE CPU big CPU GPU

GLNNNNNN

GNNNNNNB

GNNNNNNL

NNNNNNNB

B

B

B

B

L

L

L

L

1.2

0.408

0.816

0.6

1.416

1.608

1.2

1.008

0.6

0.6

0.4

0.2

34.99

40.26

42.88

47.21

243.46

226.39

208.89

191.55

Table 6.4: Extra-functional characteristics (inference time and energy per frame) of

AlexNet in Pipeline mode, focusing on processor frequency settings.

Layers mapping

Host

Frequency (GHz)

Time (ms)

Energy (mJ)

GPU NPU LITTLE CPU big CPU GPU

GNNNNNNL

GNNNNNNL

GNNNNNNL

GNNNNNNL

GNNNNNNL

GNNNNNNL

GNNNNNNL

GNNNNNNL

GNNNNNNL

GNNNNNNL

GNNNNNNL

B

B

B

B

B

B

B

B

B

B

B

L

L

L

L

L

L

L

L

L

L

L

1.008

0.6

1.2

0.816

0.816

1.2

1.008

0.6

0.816

0.6

0.816

1.608

1.608

1.416

1.416

1.2

1.416

1.008

1.008

1.008

1.2

1.2

0.6

0.6

0.6

0.6

0.6

0.4

0.6

0.6

0.6

0.4

0.4

40.45

40.5

40.52

40.57

40.95

41.14

41.37

41.54

41.58

42.8

42.88

224.67

224.42

220.68

220.22

214.92

212.99

211.18

210.43

209.77

209.39

208.89

GPU, and NPU, respectively), host selection for GPU and NPU devices,
DVFS settings for each processor, and the throughput and energy efficiency.

Impact of DVFS on Throughput and Energy Efficiency

We investigate the impact of DVFS settings on inference performance
and energy consumption. Table 6.4 presents inference time and energy
consumption per frame under various DVFS settings while maintaining a
fixed layer-to-processor mapping and host selection. This allows an isolated
analysis of DVFS effects on the GPU, LITTLE CPU (first and third stages),
and big CPU (second stage). The influence of DVFS on each pipeline stage

6.5 experimental evaluation

103

depends on whether the stage acts as a bottleneck. Lowering the frequency
of a non-bottleneck stage can reduce energy consumption per frame with-
out significantly affecting throughput. Conversely, reducing the frequency
of a bottleneck stage may increase overall energy consumption due to
prolonged inference times. These findings underscore the importance of
adaptive DVFS tuning, where power settings should be dynamically ad-
justed based on pipeline characteristics.

Discussion. The results demonstrate that a well-configured pipeline
execution across CPU-GPU-NPU significantly improves throughput (FPS)
compared to single-processor execution. By enabling the concurrent execu-
tion of different CNN layers across multiple processors, the pipeline effi-
ciently utilizes available compute resources, leading to a higher number of
processed frames per second. Unlike single-processor execution, where the
workload is limited to a single compute unit, pipeline execution distributes
computations and minimizes idle time across heterogeneous hardware,
thereby improving overall system throughput.

Interestingly, pipeline execution also improves energy efficiency per
frame. While activating multiple processors increases instantaneous power
consumption, the significant increase in throughput leads to lower energy
consumption per frame. Given the idle power consumption of the en-
tire SoC, executing inference in parallel results in more efficient energy
utilization compared to sequential execution on a single processor. The
trade-off between active and idle power consumption suggests that parallel
execution, when properly configured, is inherently more energy-efficient
than single-processor execution.

To fully exploit the benefits of pipeline execution, optimizing layer-to-
processor mappings and DVFS settings is crucial. The GA-based frame-
work systematically explores different configurations, selecting optimal
mappings that balance throughput and energy consumption. By eliminat-
ing the need for manual fine-tuning, GA-based optimization provides an
automated approach to identifying well-balanced pipeline configurations.
These results demonstrate that the GA-optimized pipeline mapping, com-
bined with DVFS tuning, provides a flexible and efficient approach to
heterogeneous inference optimization. The ability to dynamically explore
the design space and find near-optimal configurations makes the proposed
framework adaptable to different workloads and hardware platforms.

104

integrated pipeline for high-throughput cnn inference

6.6

summary

This chapter explored pipeline-based heterogeneous inference for CNNs
on HMPSoCs, shifting the focus from serial execution to parallel execu-
tion to enhance throughput. We first introduced a three-stage Pipe-ALL,
distributing inference workloads across the big CPU, LITTLE CPU , and
GPU to enable concurrent processing. Our evaluation results demonstrated
that an optimal pipeline configuration significantly improves throughput
compared to single-processor inference, effectively utilizing available com-
puting resources to sustain high FPS.

The introduction of NPU integration in pipeline and energy efficiency
considerations through DVFS settings significantly expanded the design
space, necessitating an efficient search strategy. To address this complexity,
we employed a GA-based framework, which systematically explores layer
partitioning, processor selection, and DVFS settings to jointly optimize
throughput and energy efficiency. The GA-optimized pipeline achieves
high-performance inference while maintaining energy efficiency, underscor-
ing the role of automated optimization in heterogeneous inference systems.
This study provides valuable insights into multi-processor pipeline ex-
ecution, demonstrating how layer-level pipelining, energy efficiency tun-
ing, and heuristic optimization can be leveraged for high-throughput and
energy-efficient CNN inference. Future work can explore integrating quan-
tized NPUs into pipelines with accuracy trade-offs, further optimizing
pipeline configurations for dynamic workloads, and extending the pipeline
design to more diverse HMPSoCs.

Alongside the designs, optimization techniques, and exploration strate-
gies developed in this research, we have built upon and refined specialized
execution strategies—such as CPU-GPU switching, power-aware inference,
and pipeline-based execution—with practical and innovative implementa-
tions for their evaluation and deployment on heterogeneous processors.
To maximize their impact, the next chapter presents ARM-CO-UP, a re-
designed and standardized framework that unifies, organizes, and extends
these strategies into a structured, extensible platform. By enabling system-
atic experimentation for research and simplifying real-world deployment, it
ensures scalable and reproducible heterogeneous inference, advancing both
efficiency and adaptability in deep learning on modern HMPSoCs.

7

A R M - C O - U P : A R M C O O P E R AT I V E
U T I L I Z AT I O N O F P R O C E S S O R S

Deep learning inference on HMPSoCs requires a balance between perfor-
mance, power efficiency, and scalability. Throughout this research, various
specialized execution strategies have been developed—including CPU-GPU
switching, power-aware inference, pipeline-based execution, and per-layer
profiling—to optimize CNN inference across CPUs, GPUs, and NPUs.
While each of these approaches provided significant advancements in their
respective areas, their implementations were designed for specific optimiza-
tions, leading to separate tools and frameworks. To unify, standardize, and
extend these contributions, we introduce ARM-CO-UP, a comprehensive
framework designed to facilitate seamless cooperative execution across
multiple processors while ensuring scalability and ease of deployment.

ARM-CO-UP builds on the ARM-CL and supports two execution modes:
Pipeline mode, enhancing throughput by parallelizing CNN execution, and
Switch mode, reducing latency via dynamic layer-wise processor selection.
Beyond unifying execution strategies, it integrates layer-wise DVFS tuning,
CNN partitioning automation, profiling tools, and seamless NPU integra-
tion, ensuring a scalable and adaptable solution for research and real-
world deployment. As an open-source framework, ARM-CO-UP enables
researchers and developers to advance cooperative inference, supporting
the next generation of efficient DL inference on modern HMPSoCs.

This Chapter is based on:

• E. Aghapour, Y. Shen, D. Sapra, A. Pimentel, A. Pathania "ARM-CO-UP:
ARM CO-operative Utilization of Processors" [64], in ACM Transactions on
Design Automation of Electronic Systems, 2024

105

106

arm-co-up: arm cooperative utilization of processors

LITTLE CPU

DVFS

A53 Core

A53 Core

A53 Core

A53 Core

L2 Cache

GPU

DVFS

big CPU

DVFS

Core

Core

A72 Core

A72 Core

Core

Core

NPU

L2 Cache

L2 Cache

CCI Bus

DRAM

Figure 7.1: An abstract block diagram of the RK3399Pro HMPSoC within Rock Pi

N10 embedded platform.

LITTLE CPU big CPU GPU NPU (Non-Quantized)

Theoretical Max

]
S
P
F
[

t
u
p
h
g
u
o
r
h
T

60

40

20

0

AlexNet

GoogleNet

MobileNet

ResNet50

SqueezeNet

Figure 7.2: Single-processor CNN inference throughput of different processors.

7.1

introduction

HMPSoCs consolidate multiple processors, including CPUs, GPUs, and
NPUs, onto a single chip [85]. Figure 7.1 shows the RK3399Pro HMPSoC
within the Rock Pi N10 embedded platform that exemplifies this consoli-
dation. The RK3399Pro HMPSoC incorporates a hexa-core ARM big.LITTLE
asymmetric multi-core CPU, a quad-core ARM Mali GPU, and a dedicated
NPU. The ARM big.LITTLE CPU consists of two core clusters: a high-
performance, high-power dual-core big CPU and a low-performance, low-
power quad-core LITTLE CPU. The CPUs, GPU, and NPU all support on-
chip CNN inference [27].

Figure 7.2 shows performance under single-processor inference tests con-
ducted on the Rock Pi N10 embedded platform. The figure shows that the
big CPU or GPU can outperform the others in single-processor performance,
depending on the CNN. The LITTLE CPU exhibits a comparatively lower
but still noteworthy throughput. Therefore, an embedded CPU is compa-
rable to an embedded GPU in terms of performance and remains relevant
for inference in embedded platforms [28]. However, the single-processor

7.1 introduction

107

performance falls short of meeting the minimal user experience when
running on the CPU or GPU alone [86]. Therefore, embedded applications
require collaborative utilization of CPU and GPU to meet the requirements.
NPU can also provide a comparable non-quantized inference performance.
Combining CPU, GPU, and NPU for inference opens up possibilities for
high-performance inference, as shown by theoretical max in Figure 7.2.

We present the ARM-CO-UP framework that seamlessly integrates the
NPU alongside the ARM CPU and GPU in a single CNN inference binary.
ARM-CO-UP creates a streamlined backend engine that collaboratively
executes inference tasks to minimize overhead. ARM-CO-UP framework
builds on top of the ARM-CL. ARM-CL supports highly optimized single-
processor CNN inference on ARM CPUs or GPUs. ARM-CO-UP extends
this default implementation to establish a multi-processor CPU-GPU-NPU
inference environment to ensure a comprehensive utilization of computa-
tional resources. ARM-CO-UP is the first open-source framework to cooper-
atively utilize ARM-based CPUs, GPU, and vendor-specific NPUs without
the need for access to the source codes of their libraries. This approach
allows for a more cohesive and streamlined computing environment.

Throughput and latency are the two preferred metrics for measuring the
performance of CNNs [87]. ARM-CO-UP supports cooperative CPU-GPU-
NPU inference in Pipeline and Switch modes for improving CNN inference
throughput and latency, respectively. Pipeline mode inferences multiple
frames simultaneously using a multi-stage CPU-GPU-NPU pipeline to
improve throughput. Switch mode inferences one frame at a time on either
CPU, GPU, or NPU but switches between them mid-inference depending
upon the executing CNN layer to improve latency.

Another significant factor for CNN execution on embedded platforms is
the power consumption incurred during inference [54]. The ARM-CO-UP
plays a pivotal role in enhancing the power efficiency of CNN inference
by supporting layer-level DVFS. DVFS enables fine-grained control over
power consumption, optimizing resource utilization without sacrificing
performance [88]. This capability is crucial for efficient deployment of AI
solutions in resource-constrained environments.

Novel Contributions: We make the following novel contributions with

the ARM-CO-UP framework in this work.

• ARM-CO-UP allows for cooperative CPU-GPU-NPU CNN inference
on end devices in Pipeline and Switch modes to improve latency and
throughput, respectively.

108

arm-co-up: arm cooperative utilization of processors

• ARM-CO-UP automates CNN graph partitioning into sub-graphs and
subsequent sub-graphs to processors mapping at the granularity of
CNN layers.

• ARM-CO-UP provide a model-independent implementation that fa-
cilitates adding new desired models. It even works for models with
complex graphs containing branching blocks and shortcut branches
between layers.

• ARM-CO-UP presents the APIs and command line options that enable
setting the desired configuration, such as Pipeline or Switch mode,
partitioning points, mapping to the processors, number of cores in
CPU, frequency settings of big and LITTLE CPUs and GPU, host CPU
for GPU and NPU devices, etc.

• ARM-CO-UP provides a fine-granularity profiler for layer-level profil-

ing of CNNs for metrics like performance, power, etc.

• ARM-CO-UP eases the integration of any new NPU without requiring

its library source.

• ARM-CO-UP provides Python libraries that automate extracting pa-
rameters and splitting pre-trained models based on desired partition-
ing points compatible with popular frameworks, such as TensorFlow,
Caffe, Caffe2, and Keras.

Open Source Contributions: The code for the ARM-CO-UP framework
is publicly available for download at https://github.com/Ehsan-aghapour/ARM-
CO-UP under MIT license.

7.2 related work

Multi-processor CNN inference is an active research area. Most existing
works on the subject create a multi-stage software pipeline [29, 82] between
processors to improve CNN throughput. A software pipeline provides
a mechanism to trade off throughput with latency. However, a software
pipeline inherently by design cannot improve the inference latency. Some
works attempt to improve latency by altering the underlying neural net-
work [89, 90] or searching for an appropriate neural network [91, 92].
However, our work is independent of the software optimization endeavours.
The primary focus of the ARM-CO-UP is to facilitate the cooperative and
efficient utilization of processors to perform inference.

7.2 related work

109

Table 7.1: Qualitative comparison between different frameworks that support CNN

inference on generic ARM-based HMPSoCs.

Framework

CPU

GPU NPU Pipeline Switching Layer DVFS Profiling

Symmetric Asymmetric

TVM [93]

ARM-CL,ARM-
Vela [94]

Pipe-it [29]

PipeBert [95]

OmniBoost [62]

ARM-CO-UP

✓

✓

✓

✓

✓

✓

✗

✗

✓

✓

✓

✓

✗

✗

✓ ARM NPU

✗

✗

✓

✓

✗

✗

✗

✓

✗

✗

✓

✓

✓

✓

✗

✗

✗

✗

✗

✓

✗

✗

✗

✗

✗

✓

✗

✗

Model-level

✗

✗

Layer-level

Table 7.1 qualitatively compares ARM-CO-UP with similar relevant
frameworks for CNN inference on ARM-based HMPSoCs. TVM [93] and
ARM-CL [94] are the popular frameworks for high-performance CNN
inference on ARM CPUs. However, TVM and ARM-CL can only support
one CPU at a time. Therefore, they under-utilize asymmetric multi-core
CPUs. ARM-CL also support GPU-only CNN inference. ARM-CL can also
perform NPU-only CNN inference using the ARM Vela compiler. However,
ARM Vela only supports ARM NPUs such as ARM Ethos.

Authors of [29] introduce the Pipe-it framework based on the ARM-CL.
Pipe-it creates a CNN inference pipeline between LITTLE and big CPUs
of ARM big.LITTLE asymmetric multi-core CPUs. It also uses CNN micro-
benchmarks to create model-based profiles for performance prediction.
Similarly, authors of [95] introduce a framework called PipeBert based
on TVM. PipeBert also creates a CNN inference pipeline between LITTLE
and big CPUs of ARM big.LITTLE asymmetric multi-core CPUs. PipeBert
primarily focuses on pipelined inference for BERT transformers but also
supports CNN inference. Authors of [62] introduce a framework called
OmniBoost [62] based on ARM-CL. OmniBoost supports a CNN inference
pipeline between LITTLE CPU, big CPU, and GPU.

The frameworks such as ARM-CO-UP are inherently architecture-specific.
ARM-CO-UP focuses on generic ARM-based platforms. Similar comprehen-
sive CNN inference frameworks designed for other platforms, such as those
for Nvidia [83] and Qualcomm [96], are complementary and hard to com-
pare against ARM-CO-UP. Furthermore, supporting multi-processor CNN
inference [96] for multiple networks is beyond the scope of ARM-CO-UP.
ARM-CO-UP also does not support configurable CNN accelerators such as
those based on CGRAs [97] and FPGAs [98, 99]. Moreover, ARM-CO-UP
cannot distribute CNN inference workload across multiple HMPSoCs [57].

110

arm-co-up: arm cooperative utilization of processors

ARM-CO-UP operates independently of methodologies that generate
schedules for executing CNNs on heterogeneous platforms, such as SLO-
aware inference scheduler [96]. ARM-CO-UP’s primary function is to facil-
itate implementation and performance evaluation of schedules. ARM-CO-
UP is a valuable tool for any scheduler, enabling performance assessment
at intermediate stages that aid in optimal schedule development.

None of the frameworks above support both CPU-GPU-NPU pipelining
or switching as ARM-CO-UP. Furthermore, ARM-CO-UP is the only frame-
work with fine-grained per-layer DVFS and profiling support and allows
vendor-neutral NPU integration in ARM-based HMPSoCs.

7.3

background

We delve into the foundational aspects of the ARM-CL framework, with a
specific focus on its mechanisms for enabling efficient inference processing
on end devices. This exploration serves as a groundwork to understand the
subsequent advancements introduced with ARM-CO-UP.

The ARM-CL library utilizes its API to define a model architecture.
Subsequently, based on the model, it employs the backend context to create
and run an equivalent graph on the target processor. The graph manager
oversees the graph configuration and execution. Furthermore, the graph
manager is responsible for loading the input data and scheduling the
workload functions on the target processor through its backend context. We
delve next into the fundamental components of the ARM-CL framework to
provide a detailed exposition of its structure.

Network Architecture. ARM-CL APIs provide the mechanism to define
CNN model architecture. Using this API, a user can define specific layers
and their interconnections. The definition starts with establishing a stream
for the sequential addition of layers. This stream includes a graph sub-
structure whose tail the stream tracks continuously. The stream generates a
new node when an API adds a layer and attaches the node to the tail node
of the graph. Figure 7.3 shows a simple structure (Figure 7.3 (a)) and its
pseudo-code definition (Figure 7.3 (b)) in ARM-CL.

Graph. ARM-CL creates a graph corresponding to the CNN using its
established network architecture, where the primary nodes represent the
CNN layers and the tensors represent the connection between the layers.
This representation encapsulates the architecture of the defined model
and serves as the foundation for subsequent processing and computations
within ARM-CL. ARM-CL creates Const nodes and connects them to the

7.3 background

111

(a) CNN structure

1

2

3

4

5

6

7

8

9

10

11

Stream main_stream;
main_stream << Input_Layer << Conv0 << Conv1 << Conv2;
sub_stream s1(main_stream); //Create substream (branch) from Conv 2
main_stream << Conv3;
sub_stream s2(main_stream); //Create substream (brach) from Conv 3
s2 << Conv4 << Conv5;
main_stream << Conv6;
main_stream << Add(main_stream, s2);
main_stream << Conv8;
main_stream << Concat(main_stream, s1);
main_stream << FC10 << Output_Layer;

(b) CNN Pseudo-code

(c) CNN Graph

Figure 7.3: A sample CNN structure, along with its definition and graph represen-

tation in ARM-CL.

primary nodes for the trained parameters of a layer. ARM-CL considers the
trained parameters of a layer (weights and biases) to be the layer operands
along with the inputs from the other layers. Figure 7.3 (c) shows the
equivalent graph of the structure in Figure 7.3 (a). The graph contains the
nodes and tensors that execute with ARM-CL. We display only the primary
graph nodes throughout the remainder of this paper for brevity.

Node. An ARM-CL graph comprises various nodes, where each node
correlates to a distinct layer, with each node type characterized by a
specific number of inputs and outputs. For instance, the Node “Conv 3”

InputConv 2Conv 3Conv 1Conv 6Add 7Conv 8Concat 9FC 10OutputConv 4Conv 5Conv 0InputConv 0Conv 1Conv 2Conv 3Conv 6Add 7Conv 8Concat 9OutputFC 10Conv 4Conv 5WBWBWBWBWBWBWBWBWB112

arm-co-up: arm cooperative utilization of processors

depicted in Figure 7.3 (c) represents the third convolution layer “Conv
3” shown in Figure 7.3 (a). Each node links with an associated tensor for
every input or output edge. The node executes its operation on the input
tensors (operands) and subsequently populates its output tensor.

Functions. ARM-CL implements multiple variants of functions for CPU
and GPU processors for each node type. The best function variant for
a node depends on the sizing parameters of the node (inputs, weights,
and biases). It also depends upon the hardware specification of the target
processor, such as the capacities of cache levels. ARM-CL implements es-
sential deep-learning operations specific to its corresponding node through
core kernels within each function. These kernels are designed for efficient
execution on the CPU and GPU processors, leveraging technologies such as
NEON for the CPU and OpenCL for the GPU.

ARM-CL employs OpenCL for GPU functions by providing a comprehen-
sive framework for implementing and executing kernel functions on ARM
GPUs. OpenCL excels in parallel computing for the complex calculations
typically handled by GPUs. ARM-CL, in complement, employs NEON for
CPU functions in ARM architectures. NEON is a SIMD ISA extension for
high-performance parallel processing on CPUs.

Edge. ARM-CL implements edges housing a tensor to connect the graph
nodes. The edges facilitate the flow of data between nodes. Each edge has
a source and destination node, with the source node populating the tensor
and the destination node accessing and utilizing the tensor as part of the
overall computational flow. ARM-CL attributes the tensors of the Input,
Output, and Const nodes to an accessor. The accessor is responsible for
loading and pre-processing the input data and the weights. Additionally,
the Memory Manager of the backend device is responsible for storing and
managing the memory required for the tensor. Direct access to a tensor
by different processors is not always feasible due to variations in memory
configurations among processors.

Workload. ARM-CL creates a workload for the graph that loads the input
data (image), executes the primary node functions, and post-processes the
output data to generate the prediction results. The function factory of the
backend device dynamically generates the most efficient function corre-
sponding to each node based on the sizing parameters of the layer (node)
and the hardware specifications of the backend device, such as cache sizes.
The workload incorporates the accessors of Input and Output tensors, along
with the graph functions.

7.3 background

113

Graph Manager. ARM-CL has a Graph Manager responsible for setting
up the graph and executing the workload. After graph generation, the
Graph Manager selects the backend device, configures the nodes, allocates
the tensors, and calls the accessor for Const tensors to load the weights and
biases into the relevant processor memory. Subsequently, the Graph Manager
also manages the workload execution.

Scheduler. Within ARM-CL, there are separate CPU and GPU schedulers,
each tasked with managing the scheduling of work processes for their re-
spective processors. These schedulers play a crucial role in orchestrating the
distribution of computational tasks, ensuring efficient parallel processing
on both the CPU and GPU to maximize the overall performance. The CPU
scheduler is responsible for splitting the function process and scheduling it
onto the processor threads. It employs two scheduling strategies – Static and
Dynamic. The Static strategy divides data among threads for simultaneous
processing. The Dynamic strategy partitions data into chunks, with each
thread processing a chunk and requesting the next chunk upon completion.
The Dynamic approach, helped by a Feeder class, optimally utilizes the
threads, especially on cores with varying performance capabilities. The
scheduler can configure the number of threads with or without affiliation
to processing cores. The user must provide the underlying threads-to-cores
mapping function to utilize the affiliation approach.

ARM-CL schedules its OpenCL kernels using the CLScheduler in the GPU
processing workflow when a task invokes the associated function. The
CLScheduler offloads an OpenCL kernel to the GPU by placing it into the
command queue of the GPU processor. Internally, the GPU scheduler
handles the kernel execution from the command queue into the processing
resources. This transfer process between the CPU and GPU is asynchronous
and non-blocking.

Backend Context. Within ARM-CL, backend contexts are crucial in com-
putational graph execution on CPU and GPU processors. Each distinct
context tailors to its specific processor type, and selecting a processor for
the graph execution employs the corresponding backend context. Choosing
a CPU or GPU initiates the backend context for CPU or GPU, respectively.
The backend contexts are responsible for initializing and setting up their
respective processors, creating tensors, and generating functions particular
to each node. Additionally, they oversee the memory allocation for weights
and activation data during run-time, ensuring efficient computation.

CPU Backend Context. ARM-CL provides a CPU backend context to
navigate the operations tailored for the CPU execution. The context initial-

114

arm-co-up: arm cooperative utilization of processors

izes the desired number of threads in the scheduler and handles memory
allocation for tensors, focusing on weights and activation data. The function
factory selects and generates the most efficient variant of implemented
functions for each node within this context. These functions incorporate
NEON kernels optimized to facilitate basic deep-learning CPU operations.
GPU Backend Context. Similarly, a GPU backend context within ARM-
CL manages operations specific to GPU devices, initiating the OpenCL
scheduler to coordinate the deployment of OpenCL kernels. This context
involves identifying the GPU processor, assigning it to the OpenCL device,
generating an OpenCL context, and initializing the OpenCL queue for the
associated device and context. The function factory within this context opts
for the most efficient variant of implemented OpenCL functions per node.

7.4 arm-co-up framework

The ARM-CO-UP framework builds on top of the ARM-CL Library. The
original ARM-CL supports CNN inference with either CPU or GPU pro-
cessors. In contrast, ARM-CO-UP focuses on the cooperative use of the
available processors simultaneously – CPU, GPU, and NPU – for inference.
We explain next the various components in the ARM-CO-UP framework.

7.4.1 Co-operative Utilization

A CNN graph can execute with a CPU or GPU processor by default. The
distinct backend context associated with each processor does not allow for
a collaborative execution of CNN. The ARM-CO-UP introduces the concept
of sub-graphs for simultaneous model inference with different processors.
It defines sub-graphs that execute on separate processors and memory
spaces with separate backend contexts. Consequently, a sub-graph is free to
map to its processor for execution. Pipelining and switch mechanisms can
employ sub-graphs to improve the overall performance of the CNN using
multiple processors. Therefore, it becomes necessary to manage the transfer
of intermediate data between sub-graphs and coordinate the execution
of these individual sub-graphs. The ARM-CO-UP provide Receiver and
Sender nodes (and tensors) to extend the capabilities of the Graph Manager.
Sub-Graph. The ARM-CO-UP structures the model as sub-graphs rather
than a comprehensive graph determined by the target processor assigned to
its nodes. Figure 7.4 demonstrates an equivalent graph of a model and the
mapping of its nodes to the target processor. Based on the layer mapping,

7.4 arm-co-up framework

115

Figure 7.4: ARM-CO-UP partitioning of a graph into three sub-graphs to run on

three different processors.

the consecutive layers with the same target processor constitute a sub-
graph. Each sub-graph has the same target processor, and a unified backend
context is established for the sub-graph on the target processor, overseeing
their execution on that specific processor. ARM-CO-UP offers users two
distinct modes for inference using sub-graphs: Pipeline and Switch mode.
Pipeline Mode. In the Pipeline mode, every sub-graph operates as a
distinct stage in the overarching pipeline. As a sub-graph concludes its
workload execution, it transmits its data and either commences processing
the subsequent data in its queue or momentarily halts if the input data isn’t
yet available. This mechanism ensures that the sub-graphs, representing
different pipeline stages, operate concurrently for consecutive input frames.
Such a methodology empowers users to harness processors collaboratively,
enhancing the throughput and energy efficiency of the inference.

Switch Mode. In the Switch mode, sub-graphs operate serially for each
frame, eliminating any parallel operation. Here, the inference process for
an image switches between processors. This mode allows the flexibility to
allocate layers to the most suitable processor, optimizing energy efficiency
and end-to-end latency for individual frames.

Sender and Receiver Nodes. The ARM-CO-UP creates sub-graphs within
different backend contexts. Therefore, data transfer is necessary between
the processors in intermediate terminal nodes of the sub-graphs. The
Sender and Receiver nodes add to the source and destination of the con-
nection between two sub-graphs. Figure 7.4 shows the Sender and Receiver
nodes in the intermediate terminals of the sub-graphs. The ARM-CO-UP

116

arm-co-up: arm cooperative utilization of processors

Figure 7.5: Structure and partitioning configuration where there are two receivers

for sender of the first sub-graph.

establishes an edge, via an associated Sender tensor, between the last node
in the source sub-graph and the attached Sender node. Additionally, within
the subsequent sub-graph, it creates an edge between the Receiver node
and the first node and creates a Receiver tensor for it.

Sender and Receiver Tensors. The Sender and Receiver tensors, integral
components within the ARM-CO-UP framework, facilitate data transfer
across processors’ backend contexts. These tensors are embedded with at-
tributes and mechanisms to synchronize and communicate data effectively.
Specifically, the Sender tensor holds Receiver tensors as its data transfer tar-
gets. Figure 7.5 shows the structure and partitioning configuration within
the ARM-CO-UP, wherein there are two receivers for the sender of the
first sub-graph. The Sender tensor in the first sub-graph dispatches data
to Receiver tensors located in both the second and third sub-graphs.

The Graph Manager delineates receiver nodes for each sender tensor,
forming sub-graphs during the setup. Subsequently, upon completing sub-
graph node tasks, the Graph Manager triggers its senders as outlined in
Algorithm 1 at the run-time. Each sender invokes the transfer function
for its linked receiver nodes. Figure 7.6 (a) depicts the transfer function’s
methodology. The methodology commences with mutex utilization to pre-
vent race conditions with the receiver thread of the destination sub-graph.
It then ascertains receiver readiness and buffer status. If the receiver awaits
data and its buffer is vacant, the sender directly transmits its tensor data
to the receiver’s memory in a different processor, simultaneously notifying
the receiver. Conversely, if the receiver is preoccupied or the buffer is non-
empty, the sender’s tensor data is queued in the receiver’s buffer.

                   InputNode 0Node 1Node 2Node 3OutputInputNode 0SenderNode 0Node 1SenderNode 1ReceiverNode 0CPUGPUNPU                   Node 2Node 3OutputReceiverNode 1ReceiverNode 0CPUGPUNPU7.4 arm-co-up framework

117

Algorithm 1: Sending Data

1 foreach sender ∈ graph.senders do
2

map(sender.tensor to main memory);
foreach receiver ∈ sender.receivers do
receiver.transfer(sender.tensor);

unmap(sender.tensor);

3

4

5

Algorithm 2: Receiving Data

1 foreach receiver ∈ graph_receivers do
2

receiver.set_ready();

3 foreach receiver ∈ graph_receivers do
4

receiver.receive_data;

The receivers in each sub-graph precede node task execution, as depicted
in Algorithm 2. Each sub-graph sets its receivers to a ready state and
initiates their receive functions. This process, illustrated in Figure 7.6 (b),
involves the receiver examining the Data_ready status. If true, it indicates
the sender has already populated the receiver’s tensor memory, requiring
no further action. If false and the buffer contains data, the receiver transfers
the earliest buffered data to its tensor memory. If the buffer is empty, the
receiver employs a condition variable mechanism (Condvar in C++) for effi-
cient wait management, pending data transfer from the source sub-graph.
Upon data transfer completion by the sender, which also sets Data_ready
to true, the receiver resumes processing.

The queue buffer of the receiver plays a pivotal role, accommodating
instances where the sender has readied the data but the receiver is not
prepared to accept it, often due to the ongoing processing of preceding data.
This buffer ensures continuous, seamless data flow between sender and re-
ceiver tensors. Consider a scenario where sub-graphs execute concurrently
in the parallel mode across consecutive frames using a software pipeline.
A branch extends from the first to the fourth stage (sub-graph). Figure 7.7
depicts sub-graphs formed based on node-to-processor mappings. Pipeline
stages process consecutive frames. While the first stage (stage0) processes
frame i, stagen processes frame (i − n). Upon completing the execution
of frame number i by the first stage, it sends data to the second and
fourth stages. However, a direct data transfer to the fourth stage is not

118

arm-co-up: arm cooperative utilization of processors

(a) transfer function: Transferring sender’s
tensor data of the source sub-graph into
the receiver of the destination sub-graph
or its buffer

(b) receive

function: Read data from its
buffer, or wait for transferring data from
the sender of the source sub-graph

Figure 7.6: The ARM-CO-UP transfer and receive functions in source and destina-

tion sub-graphs respectively.

feasible. The fourth stage has just concluded processing frame i − 3 and
must next process frame i − 2 that the third stage has just finished. Without
a buffer for the first stage to place data from frame i, it cannot process frame
i + 1 for the following two pipeline clocks. This lack of buffer causes two
stalls in the first stage of the pipeline during the subsequent clocks. These
stalls propagate to the end of the pipeline stages. As soon as the fourth
stage receives the frame i data from the third stage, it can be processed,
and the first stage can deliver the frame (i + 1) and start processing the
next frame (i + 2). Therefore, during each pipeline clock, the two stages
experience stalls, resulting in only two active stages, as opposed to all four.
Consequently, ARM-CO-UP incorporates buffers into Receiver tensors to
minimize the pipeline stalls.

Graph Management. The ARM-CO-UP extends the original ARM-CL
graph management to manage the coordination and execution of various
sub-graphs in Pipeline or Switch mode. The ARM-CO-UP equips the Graph
Manager with the list of sub-graphs, their backend contexts and workloads.
The setup of a full graph is a time-consuming process involving the prepa-
ration of the workload and loading the layer parameters into the memory
of the target processor using the corresponding backend context. ARM-CO-
UP partitions the graph into multiple sub-graphs according to the mapping

StartInput : Sender.tensorYesNOReceiver.ready?YESReceiver.buffer.empty?Receiver.tensor.map Receiver.tensor.copyFrom(Sender.tensor)Receiver.tensor.unmap Receiver.buffer.put(copy(sender.tensor))unlock(_mutex)Nolock(_mutex)EndStartNoYesData_ready?YesReceiver.buffer.empty?Receiver.tensor.copyFrom(buffer.front)EndYesData_ready?Data.ready = 0WaitNoNolock(mutex)unlock(mutex)7.4 arm-co-up framework

119

(a) Without buffer

(b) With buffer

Figure 7.7: Buffer Requirements for Pipeline Execution in a Branched Network

Structure.

of the layers to processors. Each sub-graph has its context for setup, so
the ARM-CO-UP establishes the sub-graph configurations concurrently,
effectively reducing the overall setup time. ARM-CO-UP exploits a multi-
threaded approach for executing the sub-graph workloads on their target
processors using a host CPU for each sub-graph. A thread to manage the
task execution spawns for each sub-graph and pins to the host CPU cores.
The ARM-CO-UP can select the sub-graph host(s) among the CPU core(s).
The receivers and senders are responsible for receiving and sending the
data from and to the source and destination sub-graphs, respectively.

Scheduler. A scheduler divides the workload across all available threads
within the original ARM-CL library. These threads execute across all cores
in the asymmetric CPUs [100]. However, the communication cost between
different CPUs can be prohibitively high, even though they may share
the same backend context [29]. Consequently, the ARM-CO-UP establishes
separate schedulers for the CPUs. Each CPU is an independent proces-
sor tasked with processing a specific sub-graph. The host, assigned to a
particular sub-graph, invokes the relevant scheduler, which then allocates
the sub-graph to the cores within its corresponding CPU. This strategy
reduces the need for extensive communication between CPUs. Inter-CPU
communication is reserved only for boundary layers, which relay their data
to the other CPU to process subsequent sub-graphs.

Stage 0Stage 1Stage 2Stage 3Frame 3Frame 2Frame 1Frame 0Stage 0Wait for Stage 3Stage 1Stage 2Stage 3Frame 3Frame 2Frame 1Stage 0Wait for Stage 3Stage 1Wait for Stage 0Stage 2Stage 3Stage 0Stage 1Wait for Stage 0Stage 2Wait for Stage 1Stage 3Frame 4Frame 3Frame 2Frame 3Stage 0Stage 1Stage 2Stage 3Frame 3Frame 2Frame 1Frame 0Stage 0Stage 1Stage 2Stage 3Frame 3Frame 2Frame 1Stage 0Stage 1Stage 2Stage 3Stage 0Stage 1Stage 2Stage 3Frame 6Frame 3Frame 2Frame 3Frame 3Frame 4Frame 4Frame 5Frame 3Frame 4Frame 4Frame 5Frame 4Frame 5120

arm-co-up: arm cooperative utilization of processors

Unified (LITTLE (4 cores) + big (2 cores))

Two-Stage Pipeline (LITTLE: 4 cores, big: 2 cores)

15

10

5

]
S
P
F
[

t
u
p
h
g
u
o
r
h
T

Alexnet

Googlenet

Mobilenet

Resnet50

Squeezenet

Figure 7.8: Performance comparison between unified and separate schedulers.

Figure 7.8 shows the performance benefits of using a separate scheduler
for each CPU versus a unified scheduler for multiple CPUs in an asym-
metric multi-core. The figure shows two distinct configurations: one where
inference executes jointly on a combination of LITTLE and big CPUs and
another utilizing a two-stage pipeline involving LITTLE and big CPUs. The
comparative analysis underscores the efficiency gains achieved by the two-
scheduler approach, where workload distribution and reduced inter-CPU
communication contribute to enhanced system performance.

7.4.2 Profiling

The ARM-CO-UP provides detailed profiling for both execution time and
power consumption of individual layers while taking inter-layer commu-
nication into account. Each task within the workload tracks its execution
duration. Upon request by the Graph Manager, the average execution time
across all frames is computed and relayed for reporting. The Graph Manager
monitors the timing for communication, input, and output operations.

Furthermore, ARM-CO-UP supports GPIO signals, enabling external
power measurement setups similar to the one introduced in Chapter 4.
These signals indicate the start and end of each layer’s processing, facili-
tating layer-specific power measurements. Figure 7.9 illustrates the power
measurement setup used by ARM-CO-UP for layer-wise power consump-
tion analysis. When power measurement is activated within ARM-CO-UP,
it transmits signals to the ARDUINO board, which then captures power
samples and tags them with these signals. This process ensures that ARM-
CO-UP extracts the samples corresponding to each layer’s execution cycle.

7.4 arm-co-up framework

121

Figure 7.9: An abstract diagram for integration of an external power-performance

profiling setup with a target device using ARM-CO-UP.

7.4.3 NPU Integration

The NPU is a dedicated ASIC accelerator processor integrated into the
latest edge HMPSOCs to optimize power and performance for neural
network inference. The NPU operates with lower precision operation units
for significantly higher performance and energy efficiency. Therefore, it is
essential to integrate this specialized processor with the CPU and GPU
processors in embedded devices.

The ARM-CL has no backend context for the NPU. Creating an NPU con-
text presents significant challenges, primarily because the libraries for the
NPU are not open source. Additionally, the NPU supports the execution of
networks in various formats, adding complexity in integrating a dedicated
context within ARM-CL. This lack of a standardized, accessible backend for
the NPU complicates its incorporation and utilization. However, the ARM-
CO-UP successfully incorporates NPU alongside CPU and GPU cores. The
integration of NPU in the ARM-CO-UP involves harmonizing the distinct
contexts and ensuring compatibility with several accelerators, each with
specific libraries and APIs.

ARM-CO-UP adds an interface layer to the top of the ARM-CL to achieve
NPU integration. This Python-based layer manages the sub-graphs of the
pre-trained model derived from established Python-based frameworks. The
layer also allows for an efficient extraction and conversion of the relevant
parts of the model, which are marked to execute on the NPU. Concurrently,
ARM-CO-UP integrates NPU generic functions, backend, and node classes
into the core of ARM-CL. This design allows defining the NPU configu-
ration based on the specific NPU integrated with their embedded device.
These additions strengthen the integration of NPUs into existing CPU and

 Power Profiles Target DeviceARDUINOPCARM-CO-UPLayer 0Layer 1InputSCLSDAINA260Power Supply Latency Profiles ProfiledDataLayer 2Layer 3Layer 4Read Power SampleWrite Power SampleGPIO Signal122

arm-co-up: arm cooperative utilization of processors

GPU environments. The goal is to ensure smooth integration and extend
the capabilities of ARM-CL.

We elaborate next on this newly added interface layer and its position
within the ARM-CO-UP. Additionally, we comprehensively analyze the
NPU’s generic functions, backend, and node classes, highlighting their
pivotal role in supporting accelerators without being restricted to particular
contexts and libraries.

Interface Layer. The ARM-CL, developed in C++, is tailored for optimal
efficiency on end devices. It provides specialized APIs that outline the
neural network’s architecture and layers. On the contrary, most neural
network models originate from Python-based libraries such as TensorFlow,
Keras, Caffe, PyTorch, etc. As a result, accelerators and NPUs predomi-
nantly interact with models from these libraries. Once these Python-centric
models translate into the accelerator-specific format, the accelerators offer
dedicated APIs, typically in Python and C++, that handle tasks such as
model loading, input loading, inference execution, and output extraction.
Therefore, an interface layer is required to fulfil several requirements. This
layer segments, extracts, and prepares the parts of the model that execute
within the NPU context. Based on the layer-to-processor mapping, the
interface layer extracts the NPU partitions. It adds the input and output
layers and saves the partition for the upcoming processing. Then, it converts
the extracted partition to the NPU format using the NPU-specific tools. In
this step, it quantized the NPU partitions of the model, if required.

The interface layer, for each sub-graph, provides unique terminology
based on the input and output layer indexes. This naming convention
allows the NPU node in the ARM-CO-UP to locate and load the corre-
sponding NPU-specific model partition for later execution. The ARM-CO-
UP can identify and retrieve the appropriate model sub-graphs based on
the specified partition points (input and output layer indexes). The interface
layer streamlines and automates the workflow, allowing models developed
in popular Python libraries to execute effortlessly by the ARM-CO-UP.

NPU Node. ARM-CO-UP introduces an NPU node, expanding the
available variety of node types within the ARM-CL. The method used to
create sub-graphs for the NPU is similar to those for CPU and GPU sub-
graphs, ensuring a consistent approach across the ARM-CO-UP framework.
However, since the design and functionality of NPU differ from the already
supported CPU and GPU contexts, adjustments to the NPU sub-graph are
necessary. Therefore, as depicted in Figure 7.10, ARM-CO-UP reconstructs
the NPU-target sub-graphs. For this purpose, it replaces all the internal

7.4 arm-co-up framework

123

(a) Same initial NPU sub-graph for CPU and GPU (b) Reformed sub-graph for NPU

Figure 7.10: An abstract diagram depicting the process of NPU reconstruction

within ARM-CO-UP.

nodes in the sub-graph with the NPU node and then connects all terminal
nodes and their associated tensors to this NPU node after creating an NPU
sub-graph. This approach treats the entire NPU sub-graph as a single NPU
node connected to other sub-graphs using regular edges.

The ARM-CO-UP begins by creating an NPU node. It then updates the
connections to link the terminal nodes to the sub-graph internal nodes
and then connects them to the NPU node instead. Figure 7.10 (a) displays
a sub-graph for the NPU, built using the ARM-CL API and context and
representing the model layers. Terminal nodes, shown as squares, include
Input, Receiver, Sender, and Output nodes, while the internal nodes, which
represent model layers, are shown as circles. The ARM-CO-UP disconnects
the connections between the terminal and internal nodes and removes
internal nodes. Then, it creates an NPU node with the name embedding the
starting and ending indices of the original nodes for naming convention.
Finally, it redirects the connection from the terminal nodes to the NPU
node. Figure 7.10 (b) shows the updated sub-graph after these changes.
This approach allows the creation of sub-graphs regardless of the specific
type of NPU (or accelerator) that will execute them.

The terminal nodes transfer data between the NPU and other sub-graphs.
They load input data sent by other sub-graphs into the NPU’s memory.
Subsequently, they get the output from the NPU sub-graphs and pass it
on to the next sub-graphs through the tensors of the connecting edges.
Since data formats and types might differ between NPUs and CPU or GPU
processors, these terminal nodes adjust the data type and format between
sub-graphs based on the ARM-CO-UP configuration.

NPU Backend Context. When ARM-CO-UP creates a graph (or sub-
graphs) for a neural network model, the Graph Manager produces the
workloads of these sub-graphs using the function factory of the associated
backend context. The ARM-CO-UP introduces the NPU backend context
to manage the creation and execution of the NPU-based model execution

ReceiverNode jSenderNode i+4SenderNode i+1Conv NodeiConv Nodei+1Conv Nodei+2Conv Nodei+3Conv Nodei+4ReceiverNode jSenderNode i+4SenderNode i+1NPU Node i_i+4124

arm-co-up: arm cooperative utilization of processors

function. This context comes equipped with a function factory designed
to craft an NPU function specifically for the NPU node. Notably, the NPU
backend context is a universal backend suitable for all NPUs. It establishes
a generic NPU function template, linking it to the NPU type defined.

NPU Function. The NPU function introduced in the ARM-CO-UP acts
as a versatile template that builds upon the foundational function type
present in the ARM-CL. It retains the primary characteristics of the ARM-
CL functions that invoke during workload execution. This function consists
of two parts: the configuration of the NPU by loading the model and the
execution, which handles the loading of input tensors, executing the model
sub-graph, and retrieving the outputs.

The NPU function, as a template class, accommodates a range of NPU-
specific APIs. Given that different NPUs possess distinct APIs for model
loading and execution, this method ensures that incorporating a new NPU
type is streamlined. Users can extend support to any new NPU by merely
integrating its unique API into the pre-established template associated
with a specific NPU classification. Consequently, when generating the NPU
function for an NPU Node, the ARM-CO-UP employs the definitions tied
to the NPU for model loading and execution. Beyond APIs, custom binary
implementations of the shared libraries accompany each NPU. The ARM-
CO-UP seamlessly manages the task of integrating these libraries into the
finalized executable binary. This integration allows easy incorporation of
a new NPU variant. A user only deposits the shared libraries pertinent to
that NPU in the specified NPU libraries directory (Libs/NPU/).

7.4.4 Power Manager

The ARM-CO-UP is additionally equipped with DVFS to regulate the
power consumption of the CPU and GPU during inference. ARM-CO-UP
allows adjusting of processor voltage and frequency for each sub-graph or
individual layer. In sub-graph-level DVFS, users define the DVFS levels
for each sub-graph, and the ARM-CO-UP power manager accordingly
adjusts the frequency settings for the processor assigned to each sub-
graph. ARM-CO-UP makes this adjustment using platform-specific system
commands. These commands are configurable within the power manager
to accommodate platform-specific idiosyncracies. The operational modes of
the power manager vary. In Switch mode, the power manager adjusts the
DVFS levels of the processors for the upcoming sub-graph upon completion
of the current one. In Pipeline mode, it operates differently as all sub-graphs

7.5 arm-co-up methodology (workflow)

125

(a) Sub-graph-level power manager

(b) Layer-level power manager

Figure 7.11: ARM-CO-UP power manager’s different level-based approaches.

execute simultaneously on their designated processors. ARM-CO-UP tasks
each processor with a single sub-graph in the pipeline mode. Therefore,
the DVFS levels for multiple sub-graphs on the same processor should be
identical. Hence, in Pipeline mode, it is only necessary to set the processor
frequency levels once during the initial setup.

Contrastingly, layer-level DVFS allows for more granular control, where
users can specify DVFS levels for each layer. The ARM-CO-UP system
dynamically adjusts the DVFS level of the respective processor according
to the setting chosen for each layer during the inference process. Given
the short execution time of layers, this mode necessitates a swift DVFS
mechanism to ensure minimal delay in applying the desired voltage and
frequency settings to the hardware. ARM-CO-UP incorporates a DVFS class
that can interface with a kernel-level DVFS governor. After integrating the
kernel-level DVFS governor into the kernel space, the API for the user-
defined governor is responsible for setting processor frequency within
ARM-CO-UP’s DVFS class. This integration empowers ARM-CO-UP to
modify processor frequency on a per-layer basis. As a practical example,
a kernel-level DVFS governor has been incorporated into ARM-CO-UP for
the Rock Pi N10 board to facilitate layer-level DVFS. Figures 7.11 (a) and
7.11 (b) demonstrate the DVFS mechanisms at sub-graph and layer levels,
utilizing system and kernel governors.

7.5 arm-co-up methodology (workflow)

This section delves into the methodology and workflow of the ARM-CO-UP
framework. As illustrated in Figure 7.12, the ARM-CO-UP framework first

Little CPUbig CPUGPUARM-CO-UP (0,FB,0) Sub-Graph 0 FB  FG  (FL,FB,FG)  FL  Governor  (FL,FB,FG) Power ManagerSub-Graph 1Sub-Graph 2Sub-Graph 3Sub-Graph 4big CPU GPU (Host = L)big CPULITTLE CPUNPU (Host = B)FG,FL (FL,0,FG)  (FL,0,0)  (0,FB,0)  (0,FB,0) FB FB FL FB LITTLE CPUbig CPUGPUARM-CO-UP FB  FG  (FL,FB,FG)  FL  Governor  (FL,FB,FG) Power Managerbig CPU GPU (Host = L)LITTLE CPU (0,FB0,0) Layer 0FB0 (0,FB1,0) Layer 1FB1 (0,FB2,FG2) Layer 2FB0Layer 3FB0 (FL5,0,0) Layer 4FB0 (FL5,0,0) Layer 5FB0 (FL6,0,0) Layer 6FB0 (0,FB3,FG3) 126

arm-co-up: arm cooperative utilization of processors

Figure 7.12: ARM-CO-UP design flow that utilizes CPU, GPU, and NPU.

prepares the NPU partitions of the model, adapting them based on user-
defined mapping. Second, it configures the DVFS and power management
components for the CPU/GPU. Subsequently, the creation of sub-graphs
ensues, structured according to node mapping. Finally, ARM-CO-UP per-
forms careful configuration of processors and their associated sub-graphs.
It then executes these sub-graphs in their predetermined modes.

Central to ARM-CO-UP is the Run Command, which encapsulates all user-
defined configurations for the inference procedure. The users do not need
to manually adjust the model, ARM-CO-UP, or processor settings with
this feature. Instead, they can directly utilize the Run Command options
to perform inference according to their preferences.

$ ./graph_alexnet_co_up --threads=4

--threads_little=2 --n=60 --cores=2 --

cores_little=4 --order=BBLGGNNN --mode=pipeline --frequency
=7-4-6-[3,2]-[4,4]-1-1-1

Table 7.2 provides a comprehensive list of configuration options for
executing the inference. The options encompass mapping model layers to
specific processors, choosing between pipeline or switch modes, designat-
ing the number of threads for CPUs, electing appropriate hosts for GPU
and NPU devices, modulating processor frequencies, and determining the
profiling level. Finally, ARM-CO-UP executes these sub-graphs in their
predetermined modes. We delve deeper into each stage: Pre-Setup, Sub-
Graph Creation, Setup, and Run Inference.

P3P3P3OutRRGPU(3.a) Graph Manager (Setup)Input, ReceiverFunctionsOutput, SenderCPURSNPU Node(4.a) Graph Manager (Run)PipelineGPUNPU Buffer NPUSub-Graph1Sub-Graph4GPUSerialNPUNPUbigCPUSub-Graph1RSNPU NodePythonModelRun ScriptPartition Extractor Prepare NPU PartsNPUPartition 1NPU Tool(1.a) ExtractQuantizedNPUPartition 2(2.a) Initializer Initialize Setup Run(2.b) Graph Creator: Create SubgraphsG1G2G3NPUCPUP2P2SP2P2RP1P1P1SSInRunConfigurationQuantizedNPUPartition 1G4P1P1SP1RNPUSampleImages(1.b) Quantize & TuneARM-CL Context(1.b) Quantize & TuneNPUPartition 2(2.c) NPU ReconstructorInitialized SubgraphsP1P1P1InP1P3P3OutP2P2P2P2P1P1P3Target Model Buffer bigCPU Buffer Sub-Graph2Sub-Graph3Sub-Graph2Sub-Graph3Sub-Graph41234Input, ReceiverFunctionsOutput, SenderNPUInput, ReceiverFunctionsOutput, SenderNPUInput, ReceiverFunctionsOutput, SenderGPU7.5 arm-co-up methodology (workflow)

127

7.5.1 Pre-Setup

The ARM-CO-UP framework begins its operational sequence by preparing
the model according to the desired mapping. Initially, it identifies and
transforms the segments of the model designated for the NPU via the
interface layer. It achieves this by isolating the specified segments from
the original Python-based model and then appending them with necessary
input(s) and output(s). It then translates these isolated segments into a
format compatible with the target NPU. During this transformation phase,
it applies an optional quantization step depending on the user preferences.
It saves each process segment under a distinctive naming convention to
ensure seamless identification in subsequent phases. The naming comes
from the starting and ending layers. This systematic naming approach
facilitates ARM-CO-UP’s ability to locate swiftly the pertinent segments.

Beyond model preparation, ARM-CO-UP also undertakes system-level
initialization. ARM-CO-UP then configures the DVFS governor and ac-
tivates power measurement components. If the user opts for additional
configuration capabilities, ARM-CO-UP spawns a DVFS object instance, em-
powering users to tweak the DVFS settings of the processors. Concurrently,
it also establishes the GPIO pins earmarked for signal transmission.

7.5.2 Sub-Graph Creation

Following the model preparation and power management configuration,
ARM-CO-UP initializes sub-graphs by the chosen mapping per model layer.
When adding the layers, a corresponding node is instantiated and incorpo-
rated into the designated sub-graph. ARM-CO-UP takes charge of this node
addition process, ensuring that each node is aptly placed within its relevant
sub-graph and automatically creates the required interconnections.

The ARM-CL algorithm uses a single graph for the entire model con-
taining all nodes and edges. In contrast, the ARM-CO-UP allows adding
nodes and edges to specific sub-graphs and automatically creates intercon-
nections between different sub-graphs. ARM-CO-UP examines the input
nodes associated with the node before adding it to a sub-graph. If an input
node is missing in the current sub-graph, an interconnection is established
between the source node and the new node, even if they belong to different
sub-graphs. ARM-CO-UP appends a Sender node to the source node (in the
source sub-graph) and inserts a Receiver node before the new node (in the
target sub-graph) to achieve this. The address of the Sender tensor (with the

128

arm-co-up: arm cooperative utilization of processors

Table 7.2: Configuration Attributes for Inference Run Commands

Attribute

Purpose

Details

order

Maps layers to processors

Determine the processor type for each layer. ‘L’
for LITTLE CPU, ‘B’ for big CPU, ‘G’ for GPU,
and ‘N’ for NPU.

mode

Defines execution mode

Either ‘Pipeline’ or ‘Switch’

threads

Number of threads for big CPU

Number of threads within big CPU, that dis-
tribute tasks of a layer to them (from 1 to the
number of big cores)

cores

Number of cores in big CPU of the
platform

For platforms with different number of cores in
big CPU

threads_little Number of threads for LITTLE CPU

Number of threads within LITTLE CPU, that
distribute tasks of a layer to them (from 1 to
number of LITTLE cores).

cores_little

Number of cores in LITTLE CPU of
the platform

For platforms with different number of cores in
LITTLE CPU

n

Number of frames

frequency

Frequency of the layers/sub-graphs

host_gpu

The host processor for GPU device

host_npu

The host processor for NPU device

profile

Set the level of profiling

To set the number of frames that run the infer-
ence (is useful for measuring the average perfor-
mance metrics)

Frequency indexes
layers/sub-graphs

separated with ‘-’

for

Either ‘B’ or ‘L’ that means big or LITTLE CPU,
respectively

Either ‘B’ or ‘L’ that means big or LITTLE CPU,
respectively

The possible profiling levels are Level 0: report-
ing the overall latency and throughput, Level 1:
execution and transfer time of the sub-graphs,
and Level 2: execution and transfer time for each
layer

Sender node) is in the Receiver tensor (with the Receiver node). It saves
the address of the Sender tensor in the Receiver tensor associated with the
Receiver node. This step ensures data communication and synchronization
between these nodes during run-time. ARM-CO-UP tracks the mapping of
nodes to their Sender and Receiver nodes. Subsequent nodes can directly
use this existing Receiver node for interconnection, rather than creating
a new one, if the Receiver node for an input node already exists in the
current sub-graph. This automated, model-independent graph creation pro-
cess enables the algorithm with new models without significant additional
effort. Furthermore, this mechanism is effective even for complex models
with branches and shortcuts, such as in Figure 7.4.

7.5 arm-co-up methodology (workflow)

129

ARM-CO-UP provides scalable and efficient sub-graph management by
creating sub-graphs within the core of the ARM-CL. Consequently, intro-
ducing new models becomes straightforward, eliminating any need to alter
the existing model code. ARM-CO-UP refines the NPU sub-graph once
it has established the sub-graphs. It accomplishes this by substituting its
internal nodes with a singular NPU node.

7.5.3 Sub-Graph Management

Graph Manager within ARM-CO-UP sets up and executes the sub-graphs.
Original ARM-CL works with a single graph representing the model. How-
ever, in ARM-CO-UP, multiple sub-graphs are set up on different processor
types, and these sub-graphs can execute in Pipeline or Switch mode.

Setup. In the setup phase, after setting up the backend context, the Graph
Manager creates and initializes all tensors associated with each edge of
the sub-graph on their respective target processors. It generates a Memory
Manager for each processor and tasks the manager to handle the tensors
buffer within the corresponding backend context. Meanwhile, for each
node, ARM-CO-UP leverages the function factory of the backend context,
creating optimized functions tailored for individual nodes. This process
generates workload for each sub-graph. Further, the NPU backend creates
the function for the NPU node based on the user-defined NPU type.

enum class NPUTypes{

RockPi,

Khadas,

};

const NPUTypes selectedNPU = NPUTypes::RockPi;
create_npu_function<NPU<selectedNPU>>(node);

ARM-CO-UP adds the execution tasks represented by node function
input and output tensors to the workload. The input tensor’s accessor
handles the loading and pre-processing of the input data (image), while the
output tensor accessor is responsible for post-processing and interpreting
the output. ARM-CO-UP extends the workload by adding the Receiver
and Sender tensor of the Receiver and Sender nodes, respectively. These
extended objects facilitate the synchronization and transfer of data. The
subsequent phase involves memory allocation for Constant tensors, which
house essential parameters such as weights and biases. Once allocated,
ARM-CO-UP begins the loading process for these trained static parameters.
These static parameters require a one-time load during the setup phase,

130

arm-co-up: arm cooperative utilization of processors

preparing the system for inference across varied input images. Since ARM-
CO-UP sets up sub-graphs in parallel, it reduces the loading time.

In parallel, ARM-CO-UP addresses the NPU segments of each sub-
graph (extracted earlier in the pre-setup phase). Leveraging the distinctive
naming convention, the pertinent NPU node — tasked with executing that
specific segment — identifies and retrieves its associated segment. With
the workloads for each sub-graph now defined and the model’s static
parameters duly loaded, ARM-CO-UP stands poised to execute inference
on the provided input images.

Run the Inference. ARM-CO-UP framework loads the input data and
executes the inference workload functions in the run step. In terms of
execution, the graph management run component of the ARM-CO-UP
includes the execution of inter-connection tensors involving the receiver
and sender. Each sub-graph host, pinned to a specified CPU core, handles
the sub-graph workload autonomously. This host thread activates the tensor
accessors for input and receivers, ensuring data is seamlessly fetched from
the primary input or dispatched from sender sub-graphs, as needed. ARM-
CO-UP systematically schedules the workload functions of the sub-graph
on the target processor once it has prepared all data elements. Subsequently,
it engages the tensor accessor for all outputs and senders, facilitating the
post-processing of output results and the data forwarding to the receiving
sub-graphs to continue the inference. The run procedure extends to the
execution of the receiver-tensor function at the beginning (in addition to
the input tensor functions) and the sender-tensor function at the end of
each sub-graph (in addition to the output-tensor function). The Receiver
and Sender tensors transfer data between sub-graphs and synchronize their
execution due to the dependencies. The sender-tensor holds the address of
the receiver tensors to which it sends the data. Once the data is ready, the
sender-tensor calls the send_data function of all associated receiver tensors
and passes the data as an input argument. This function checks if the
receiver can receive the data. If it is ready, then the sender-tensor transfers
data to the receiver-tensor. If the receiver is unprepared, the sender-tensor
places the data in the buffer of the receiver-tensor before returning.

On the other hand, the Graph Manager initiates the execution of a sub-
graph by calling the functions of the Input and Receiver tensors. The
Receiver tensor then calls the receive_data function, which checks if
data is in the buffer. If data is available, the Receiver tensor fetches it;
otherwise, the Receiver tensor sets the ready flag and waits for the sender
to send the data. Though the execution of each sub-graph is managed by

7.6 validation

131

a separate host thread, harnessing a multi-threaded approach, these sub-
graphs represent sequential segments of the complete model, necessitating
consecutive execution. This structure precludes parallel execution of sub-
graphs for a single input image. However, the design does permit parallel
processing of successive input images, leveraging a pipeline structure.

By incorporating these enhancements, ARM-CO-UP enables efficient and
collaborative utilization of various processor types, enhancing performance,
energy efficiency, and flexibility.

7.6 validation

Determining the optimal mapping of every layer to the appropriate proces-
sor is crucial in achieving desired performance outcomes within the con-
straints of a given application. ARM-CO-UP offers a versatile set of features
to navigate this massive search space effectively while enabling the fine-
tuning of inference performance for specific targets. The key feature of the
ARM-CO-UP is the ability to map layers to processors, allowing for desired
allocation and optimization based on application objectives. The profiling
functionality is the foundation for exploring the mapping search space in
the ARM-CO-UP framework. In addition, ARM-CO-UP provides options
for selecting the running mode (Pipeline or Switch) to facilitate cooperative
processor utilization, adjusting processor frequencies at a granular level
for power management, specifying the number of threads for CPUs, and
designating the host CPU for GPU and NPU devices.

The primary performance, power, and accuracy results for the Pipeline,
Switch mode, and DVFS strategies have already been presented mainly in
previous chapters. Here, we provide a complementary analysis, showcasing
additional profiling insights at the layer level across different processors
(CPU, GPU, and NPU). This detailed profiling offers further understanding
of the framework’s capabilities, particularly in exploring the efficiency of
different processors in executing individual CNN layers.

7.6.1 Case Study

We leverage the capabilities of the ARM-CO-UP framework to present intu-
itive analytical results. Our case study analysis focuses on the timing and
power consumption of the MobileNet CNN, utilizing the profiling feature
of the framework. The analysis applies to other CNNs in a similar manner.
Initially, we delve into the power efficiency (Frames Per Second per Watt -

132

arm-co-up: arm cooperative utilization of processors

408 MHz

600 MHz

816 MHz

1008 MHz

1200 MHz

1416 MHz

]
t
t
a

W
/
S
P
F
[

y
c
n
e
i
c
fi
f
E
-
r
e
w
o
P

]
t
t
a
W
/
S
P
F
[

y
c
n
e
i
c
fi
f
E
-
r
e
w
o
P

]
t
t
a
W
/
S
P
F
[

y
c
n
e
i
c
fi
f
E
-
r
e
w
o
P

]
t
t
a
W
/
S
P
F
[

y
c
n
e
i
c
fi
f
E
-
r
e
w
o
P

40

20

40

20

40

30

20

10

60

40

20

0

1

2

3

4

5

6

7

8

9

10

11

12

13

Layer

(a) LITTLE CPU

408 MHz

600 MHz

816 MHz

1008 MHz

1200 MHz

1416 MHz

1608 MHz

1800 MHz

0

1

2

3

4

5

6

7

8

9

10

11

12

13

Layer

(b) big CPU

200 MHz

300 MHz

400 MHz

600 MHz

800 MHz

0

1

2

3

4

5

6

7

8

9

10

11

12

13

Layer

408 MHz

600 MHz

816 MHz

(c) GPU
1008 MHz

1200 MHz

1416 MHz

1608 MHz

1800 MHz

0

1

2

3

4

5

6

7

8

9

10

11

12

13

Layer

(d) NPU

Figure 7.13: Power efficiency vs. Frequency for MobileNet layers.

7.6 validation

133

LITTLE CPU big CPU GPU NPU (Quantizied)

102

101

]
s

m

[

e
m
T

i

102.5

102

101.5

]
J

m

[

y
g
r
e
n
E

]
t
t
a
W
/
S
P
F
[

y
c
n
e
i
c
fi
f
E
r
e
w
o
P

101.5

101

100.5

0

1

2

3

4

5

6

7

8

9

10

11

12

13

Layer

(a) Time

0

1

2

3

4

5

6

7

8

9

10

11

12

13

Layer

(b) Energy

0

1

2

3

4

5

6

7

8

9

10

11

12

13

Layer

(c) Power Efficiency

Figure 7.14: Different characteristics of MobileNet layers on different processors.

FPS/Watt) of individual layers for exploring various DVFS levels through
the ARM-CO-UP power manager. Subsequently, we conduct a comparative
analysis of the execution time, energy consumption, and power efficiency
across different processors for each layer. This comparative study sheds
light on the performance and efficiency of processors concerning diverse
layers within the MobileNet architecture. Users can utilize these results to
facilitate the identification of the optimal inference configuration based on
the specific objectives and constraints of their application.

134

arm-co-up: arm cooperative utilization of processors

Figure 7.13 illustrates the power efficiency of MobileNet layers across vari-
ous frequency levels for the LITTLE CPU, big CPU, GPU, and NPU. Notably,
for the NPU, the exploration is conducted concerning the host (big CPU)
frequency, given that the NPU lacks DVFS level adjustment capabilities (see
Figure 7.13 (d)). This experiment leverages the profiling feature at the layer
granularity, coupled with the power manager, to measure the time and
power consumption of layers under different DVFS settings. Subsequently,
we calculate the power efficiency of each layer.

The results reveal a general trend across the LITTLE CPU (Figure 7.13 (a)),
big CPU (Figure 7.13 (b)), and GPU (Figure 7.13 (c)), wherein increasing the
frequency enhances the power efficiency of layers. We attribute this phe-
nomenon to the reduction in time, which outweighs the increase in power,
resulting in higher power efficiency and reduced final energy consumption.
However, the dynamics differ for the NPU (Figure 7.13 (d)). Given that
the explored frequency is not that of the NPU itself but rather the host
CPU (big CPU), the results indicate that, when running layers on the NPU,
the optimal choice for maximizing power efficiency is to minimize the
frequency of the host CPU.

In the context of the NPU, it is crucial to delineate the distinct role of the
host CPU, particularly the big CPU cluster, which orchestrates the loading
of input data into the NPU and initiates its execution. It is important to
note that altering the frequency and voltage settings of the host CPU does
not directly impact the execution time of a layer on the NPU. Instead, any
increase in the CPU frequency and voltage settings amplifies the HMPSoC’s
power consumption, as the CPU voltage heightens during NPU execution,
consequently increasing power and compromising overall efficiency.

In the subsequent assessment, we delve into the efficiency of the LITTLE
CPU, big CPU, GPU, and NPU across different layers of the MobileNet, with
the results of this comparative analysis presented in Figure 7.14. For this
analysis, 60 random images were drawn from the ImageNet dataset for
evaluation and profiling by ARM-CO-UP. We then averaged the results
to generate the graphs. We use each image for inference individually,
i.e. with the batch size setting as one. This analysis encompasses the
examination of execution time (Figure 7.14 (a)), energy consumption (Fig-
ure 7.14 (b)), and power efficiency (Figure 7.14 (c)). The examination of
execution time depicted in Figure 7.14 (a) reveals that, in most cases, the
NPU exhibits the highest performance, significantly outperforming other
processors. The first layer is an exception, where the NPU’s superiority is
mitigated by the substantial contribution of loading and preparing input

7.6 validation

135

big to LITTLE
GPU to big

LITTLE to big
LITTLE to GPU big to GPU

GPU to LITTLE

8

6

4

2

]
s

m

[

e
m
T

i

0

1

2

3

4

5

6

7

8

9

10

11

12

Layer

Figure 7.15: Inter-processor transfer times for MobileNet layers

data. The NPU effectiveness is reduced by the overhead of transferring
data, especially for initial layers with large data sizes. Furthermore, the
results indicate comparable performance between the CPU and GPU, with
the CPU outperforming in some layers and the GPU excelling in others.
This nuanced performance distinction underscores the intricacies of layer-
specific computational requirements and the adaptability of the processors
to varying tasks within the MobileNet architecture.

The results for energy consumption (Figure 7.14 (b)) and power efficiency
(Figure 7.14 (c)) underscore that the NPU not only surpasses the CPU and
GPU in terms of performance (execution time) but also exhibits optimal
energy consumption and power efficiency. This observation implies that
the NPU is the most effective processor for performance and power effi-
ciency. However, when the target is throughput, using the Pipeline mode,
incorporating both the CPU and GPU contributes to increased throughput
compared to utilizing only the NPU. A trade-off exists between accuracy
and performance/power efficiency, even in the Pipeline mode. This obser-
vation is because NPU computations are executed in a quantized version,
leading to a drop in accuracy. Striking a balance between these factors
becomes pivotal in optimizing the overall system performance based on
specific application requirements and objectives.

Figure 7.15 investigates the transfer time between different source and
destination processors for MobileNet layers. These timings serve as a mea-
sure of overhead incurred during the switching process between different
processors. Notably, the transfer time is contingent upon the data transfer
size. The data transfer involves direct movement, conducted in switch mode
(without buffering), from the output of one layer in the source processor to
the input of the next layer in the target processor. This process encompasses
synchronization overhead, accentuating the communication overhead dur-

136

arm-co-up: arm cooperative utilization of processors

ing the transition between successive layers. Figure 7.15 illustrates that this
transfer time tends to decrease as we progress deeper into the network.
This observation stems from the fact initial layers typically involve larger
data sizes for transfer, while deeper layers exhibit a decrease in data size.
Observations suggest that transitioning to other processors in deeper layers,
especially for those with higher switching costs, is more advantageous.

Furthermore, the transfer time for MobileNet ranges approximately from
one to five milliseconds, as depicted in Figure 7.15. This range, when
compared to the order of execution times for layers on processors (Fig-
ure 7.14 (a)), indicates that tolerating overhead for switching between
processors every couple of layers could be beneficial. The relatively low
overhead associated with switching stems from the integrated nature of
these processors on a single chip. This insight into transfer times provides
valuable guidance for optimizing the layer distribution across processors,
accounting for the trade-off between computational efficiency and the cost
of inter-processor communication.

A comprehensive examination of the execution costs at various layers
enables seamless integration with design space exploration algorithms. This
examination underscores the adaptability of the framework, empowering
users to customize the inference process according to their specific applica-
tion requirements through optimization and search algorithms.

7.7

summary

In this chapter, we presented ARM-CO-UP, a comprehensive and extensible
framework that advances multi-processor CNN inference on heterogeneous
end devices. By cooperatively utilizing ARM CPUs, GPUs, and NPUs, ARM-
CO-UP supports optimizing inference performance and efficiency. Unlike
state-of-the-art solutions, ARM-CO-UP supports accelerators alongside con-
ventional CPUs and GPUs, efficiently handles complex CNN models, and
enables seamless execution across diverse hardware configurations.

The framework introduces a refined and extensible implementation
within the core of ARM-CL, significantly expanding its capabilities. It
offers fine-grained layer-level partitioning, layer-wise DVFS tuning, auto-
mated handling of branched CNN architectures, and a generic NPU node
for effortless accelerator integration. These features make ARM-CO-UP a
practical and scalable solution for optimizing DL inference on resource-
constrained end devices.

8

C O N C L U S I O N

This PhD thesis presented research performed by the author towards
efficient DL inference on end devices equipped with HMPSOCs. This
thesis sets out to address the challenges of deploying DL inference on
resource-constrained end devices by exploiting the heterogeneous capa-
bilities of modern HMPSoCs. In particular, the research focused on op-
timizing inference latency, power efficiency, accuracy, and throughput
through novel strategies that leverage the diverse characteristics of CPUs,
GPUs, and emerging NPUs. The work has spanned multiple interconnected
themes—from layer-level processor switching and DVFS to partial quantiza-
tion and pipeline-based execution—and has culminated in the development
of a unified framework for cooperative processor utilization, ARM-CO-UP.
This final chapter consolidates the findings, methodologies, and insights
developed throughout the thesis. It is divided into three sections. The
first highlights the main contributions to DL inference on HMPSoCs. The
second offers a reflective set of answers to the original research questions,
interpreting how the results and frameworks proposed in this work address
the challenges posed at the outset. Lastly, it proposes several directions for
future work, underscoring the opportunities that remain to be explored.

8.1 contributions

research advances

This
in deploying DL mod-
the state-of-the-art
els—especially CNNs and DNNs—on resource-constrained end devices
equipped with CPUs, GPUs, and NPUs. The key contributions are
summarized as follows:

1. Layer-Level Processor Switching for Latency Reduction. This work
identifies that different layers in CNNs exhibit distinct computational
characteristics, making them more suitable for execution on either the
CPU or GPU. A dynamic layer-switching mechanism was designed

137

138

conclusion

and implemented to assign each CNN layer to the optimal processor,
thereby reducing inference latency. Experimental evaluations on the
Khadas VIM 3 board with an Amlogic A311D HMPSoC demonstrated
an average latency reduction of 4.72% compared to conventional
single-processor strategies.

2. PELSI Framework. Building on the latency optimization work, we
developed the PELSI framework that exploits the layer-wise power
efficiency heterogeneity on HMPSoCs. By integrating per-layer DVFS
and CPU-GPU switching with a GA to navigate an exponential design
space, PELSI identifies near-optimal configurations that meet latency
targets while minimizing power consumption. Evaluations on the
Rock-Pi N10 platform with an RK3399Pro HMPSoC demonstrated
improvements in power efficiency of up to 44.48% relative to state-
of-the-art approaches.

3. PiQi Framework. Recognizing the substantial performance and
power advantages provided by NPUs—which are often limited by
the constraints of quantized inference—we introduced the PiQi
framework. PiQi enables partial quantization, allowing different
layers of a DNN to be executed in full precision on the CPU/GPU or
in quantized form on the NPU. A multi-objective GA, complemented
by an accuracy prediction model, is used to identify configurations
that yield a favorable power-performance Pareto front under user-
defined accuracy constraints. This work extends the applicability
of NPUs in scenarios where high accuracy is required while still
benefiting from their efficiency.

4. Integrated Pipeline for High-Throughput Inference. While early
chapters focused on serial execution improvements, the thesis also
explores parallel execution through a pipelined inference approach.
We designed a three-stage pipeline that spans an ARM’s big.LITTLE
CPU’s big and LITTLE clusters and the GPU, and later considered
integration of NPUs. Using GA-based optimization to jointly adjust
layer partitioning, DVFS settings, and processor assignments, the
pipeline-based approach significantly increased throughput and im-
proved energy efficiency per frame over single-processor strategies.

5. ARM-CO-UP: A Unified Framework for Cooperative Inference.
The diverse strategies developed throughout this work are brought
together in the ARM-CO-UP framework—a comprehensive tool for

8.2 answers to the research questions

139

cooperative inference on HMPSoCs. ARM-CO-UP supports both
pipeline and switch modes, automates layer-level graph partitioning
and processor mapping, and provides fine-grained profiling and
DVFS control. Its modular design and open-source availability under
the MIT license make it a valuable resource for both the research
community and industry practitioners seeking to deploy efficient DL
models on end devices.

8.2 answers to the research questions

At the outset, the thesis posed four questions centering on how to optimize
performance, power, and accuracy when running DL models on heteroge-
neous devices under varying constraints. Having validated the proposed
strategies through extensive experimentation, it is now possible to reflect
on these questions in a conclusive manner.

RQ1: Given the critical role of responsiveness in real-time applications, what
strategies can be employed to minimize inference latency on conventional HMP-
SoCs equipped with CPU clusters and GPUs?

Findings across multiple experiments show that a layer-by-layer mapping
of CNN workloads to CPU or GPU offers a practical and effective solution
to reduce inference times. Empirical latency measurements indicated that
certain layers, especially those featuring heavy convolutional operations,
perform better on the GPU, while others that are less parallel or require
frequent memory accesses can benefit from CPU execution. Despite incur-
ring additional overhead for device switching, the aggregated runtime still
proves lower than using a single processor throughout. Consequently, this
layer-switched technique provides a tangible reduction in latency, which
is particularly evident when executing deeper CNNs or applications with
tight real-time constraints.

Moreover, the results point to a nuanced understanding of how each
layer’s arithmetic intensity and size profile affect CPU-GPU utilization. For
example, smaller memory-bound layers often exhibit minimal gain from
GPU parallelism and run faster on the CPU. By fusing such insights into
a unified scheduler, latency remains at or below stringent targets set by
tasks like AR or interactive robotics, thus confirming the efficacy of tailored
layer-switching solutions.

140

conclusion

RQ2: How can we optimize inference power efficiency while meeting target

latency requirements on HMPSoCs?

The experiments demonstrated that merging the layer-switched concept
with DVFS offers a strong route for controlling power usage without
jeopardizing performance. Profiling each layer’s runtime at different clock
frequencies allowed identifying where reduced voltage and frequency
settings could still meet end-to-end deadlines. The evolutionary search-
based method (for example, using GAs) systematically scanned possible
configurations, revealing that carefully lowered frequency levels in specific
layers lead to significant power reductions (commonly above 40% in some
benchmarks) without missing the overall latency target.

These findings validate that frequent scaling is most effective when
guided by layer-specific performance data. In scenarios such as long-
running mobile applications, the ability to remain within a strict power
envelope while sustaining responsiveness makes DVFS-based optimization
a critical pillar. Hence, for end devices reliant on battery capacity or
restrictive power budgets, the synergy of layer-switching and DVFS is a
valuable model for balanced, efficient deep learning inference.

RQ3: How can emerging neural network accelerators (e.g., NPUs) be leveraged
to explore accuracy-performance-power trade-offs and find the optimal balance for
target accuracy in end devices?

Tests conducted with partial quantization exhibited the substantial gains
of NPUs in achieving high throughput and low power consumption, at the
cost of some accuracy loss if everything is quantized. To address this, the
framework selectively quantizes only the layers robust to reduced precision
while keeping those that are accuracy-sensitive in full precision on CPU
or GPU. This combination fosters an optimal path between uniform, full-
precision inference (which can be resource-intensive and slow) and uniform,
all-Int-8 inference (which may yield unacceptable accuracy). The measured
results validate that partial quantization maintains accuracy close to all–full-
precision models while delivering power consumption and inference-speed
improvements more akin to fully quantized designs. Consequently, NPUs
become integral rather than optional in devices that need advanced AI
functionalities but must also stay within tight power or thermal envelopes.

8.3 future work

141

Empirical metrics underscore the importance of layer-level profiling: not
all parts of a CNN contribute equally to final accuracy, so tailoring a
partial quantization map to each network architecture can significantly
expand the design space. This variety of configurations suits different prior-
ities—such as minimal battery drain, real-time performance, or maximum
precision—making NPUs both powerful and flexible platforms for next-
generation AI in the edge devices.

RQ4: How can we improve inference throughput and power efficiency with

minimal latency overhead in HMPSoCs?

Real-world industrial and consumer applications often need to process
data streams at high frame rates while maintaining low average latency.
Pipeline-based scheduling complements layer-switching by allowing multi-
ple processors to work in parallel on separate frames or sub-graphs at the
same time. The reported improvements in FPS showed that pipelining can
increase throughput considerably, especially for multi-stage tasks or large-
batch processing. This pipeline execution also tends to improve energy
usage per frame because hardware resources remain more consistently
active in parallel rather than alternating between idle and high-load states.
Analyses revealed that constructing such pipelines benefits from strate-
gies like intelligent partitioning of the model, dynamic synchronization,
and minimal overhead in data transfers. Each sub-graph can run on the
processor best suited to that stage, leading to a blended pipeline where big
CPUs, LITTLE CPUs, GPUs, and NPUs all contribute to overall through-
put gains. When combined with partial quantization or DVFS as needed,
pipeline-based approaches successfully boost capacity to handle extensive
inputs, a valuable asset for tasks like real-time video analytics on mobile or
embedded platforms.

8.3

future work

Building on these insights, one important direction for future work involves
dynamic runtime reconfiguration, in which policies for layer assignment,
DVFS levels, or quantization settings adapt to shifting workloads and
resource conditions. Such systems could respond to variations in data
complexity, battery levels, or user-driven priorities, making them more
robust in environments where demands change frequently.

142

conclusion

An additional prospect is to explore accuracy and throughput trade-offs
in pipeline mode, extending the partial quantization and DVFS strategies
beyond serial or layer-switched executions. Many applications have both
frame-rate and accuracy demands, so orchestrating these variables in a
pipeline context could unlock even more efficient concurrency and deeper
optimization of overall performance or power profiles.

Moreover, emerging transformer-based models represent a fast-growing
domain that surpasses typical CNN footprints in size and complexity.
Future frameworks that adapt the proposed pipeline, switching, and quanti-
zation schemes to these large-scale architectures may substantially broaden
practical on-device inference capabilities, delivering advanced AI functions
in contexts where cloud connectivity is limited or insufficient.

The methods described here serve as a foundation for building versatile,
high-performance, power-aware DL solutions that run locally on HMPSoCs.
By bridging hardware heterogeneity with refined layer-level scheduling, ad-
vanced quantization, and dynamic power management, the field is poised
to further accelerate the adoption of AI-driven applications in portable,
embedded, and resource-limited environments.

B I B L I O G R A P H Y

[1]

Iqbal H Sarker. “Deep Learning: A Comprehensive Overview on Techniques, Tax-
onomy, Applications and Research Directions.” In: SN Computer Science 2.6 (2021),
p. 420. doi: 10.1007/s42979-021-00815-1.

[2] Kh Shahriya Zaman, Mamun Bin Ibne Reaz, Sawal Hamid Md Ali, Ahmad Ashrif
A Bakar, and Muhammad Enamul Hoque Chowdhury. “Custom Hardware Archi-
tectures for Deep Learning on Portable Devices: A Review.” In: IEEE Transactions
on Neural Networks and Learning Systems 33.11 (2021), pp. 6068–6088. doi: 10.1109/
TNNLS.2021.3082304.

[3] Long Cheng, Yan Gu, Qingzhi Liu, Lei Yang, Cheng Liu, and Ying Wang. “Advance-
ments in Accelerating Deep Neural Network Inference on AIoT devices: A Survey.”
In: IEEE Transactions on Sustainable Computing (2024). doi: 10 . 1109 / TSUSC . 2024 .
3353176.

[4] Anais Boumendil, Walid Bechkit, and Karima Benatchba. “On-Device Deep Learn-
ing: Survey on Techniques Improving Energy Efficiency of DNNs.” In: IEEE Trans-
actions on Neural Networks and Learning Systems (2024). doi: 10 . 1109 / TNNLS . 2024 .
3430028.

[5] Di Liu, Hao Kong, Xiangzhong Luo, Weichen Liu, and Ravi Subramaniam. “Bring-
ing AI to Edge: From Deep Learning’s Perspective.” In: Elsevier Neurocomputing 485
(2022), pp. 297–320. doi: 10.1016/j.neucom.2021.04.141.

[6] Umut Güçlü and Marcel AJ Van Gerven. “Deep Neural Networks Reveal a Gradient
in the Complexity of Neural Representations Across the Ventral Stream.” In: Journal
of Neuroscience 35.27 (2015), pp. 10005–10014. doi: 10 . 1523 / JNEUROSCI . 5023 - 14 .
2015.

[7] Maryam M Najafabadi, Flavio Villanustre, Taghi M Khoshgoftaar, Naeem Seliya,
Randall Wald, and Edin Muharemagic. “Deep Learning Applications and Chal-
lenges in Big Data Analytics.” In: Springer Journal of Big Data 2 (2015), pp. 1–21.
doi: 10.1186/s40537-014-0007-7.

[8] Hoo-Chang Shin, Holger R Roth, Mingchen Gao, Le Lu, Ziyue Xu, Isabella Nogues,
Jianhua Yao, Daniel Mollura, and Ronald M Summers. “Deep Convolutional Neural
Networks for Computer-Aided Detection: CNN Architectures, Dataset Character-
istics and Transfer Learning.” In: IEEE Transactions on Medical Imaging 35.5 (2016),
pp. 1285–1298. doi: 10.1109/TMI.2016.2528162.

[9] Vinod Nair and Geoffrey E Hinton. “Rectified Linear Units Improve Restricted
Boltzmann Machines.” In: Proceedings of the 27th International Conference on Machine
Learning. 2010, pp. 807–814. doi: N/A.

143

144

bibliography

[10] Chen-Yu Lee, Patrick W Gallagher, and Zhuowen Tu. “Generalizing Pooling Func-
tions in Convolutional Neural Networks: Mixed, Gated, and Tree.” In: Artificial
Intelligence and Statistics. 2016, pp. 464–472. doi: 10.48550/arXiv.1509.08985.

[11]

[12]

Sergey Ioffe and Christian Szegedy. “Batch Normalization: Accelerating Deep Net-
work Training by Reducing Internal Covariate Shift.” In: International Conference on
Machine Learning. 2015, pp. 448–456. doi: 10.48550/arXiv.1502.03167.

Song Han, Jeff Pool, John Tran, and William Dally. “Learning Both Weights and Con-
nections for Efficient Neural Network.” In: Advances in Neural Information Processing
Systems 28 (2015). doi: 10.48550/arXiv.1506.02626.

[13]

Jia Deng, Wei Dong, Richard Socher, Li-Jia Li, Kai Li, and Li Fei-Fei. “ImageNet:
A Large-Scale Hierarchical Image Database.” In: 2009 IEEE Conference on Computer
Vision and Pattern Recognition. 2009, pp. 248–255. doi: 10.1109/CVPR.2009.5206848.
[14] Alex Krizhevsky, Ilya Sutskever, and Geoffrey E Hinton. “ImageNet Classification
with Deep Convolutional Neural Networks.” In: Advances in neural information
processing systems 25 (2012). doi: 10.1145/3065386.

[15] Christian Szegedy, Wei Liu, Yangqing Jia, Pierre Sermanet, Scott Reed, Dragomir
Anguelov, Dumitru Erhan, Vincent Vanhoucke, and Andrew Rabinovich. “Going
Deeper with Convolutions.” In: Proceedings of the IEEE Conference on Computer Vision
and Pattern Recognition. 2015, pp. 1–9. doi: 10.48550/arXiv.1409.4842.

[16] Andrew G Howard, Menglong Zhu, Bo Chen, Dmitry Kalenichenko, Weijun Wang,
Tobias Weyand, Marco Andreetto, and Hartwig Adam. “MobileNets: Efficient Con-
volutional Neural Networks for Mobile Vision Applications.” In: arXiv Preprint
(2017). doi: 10.48550/arXiv.1704.04861.

[17] K He, X Zhang, S Ren, and J Sun. “Deep Residual Learning for Image Recognition.”
In: Pattern Recognition (2016), pp. 770–778. doi: 10.48550/arXiv.1512.03385.

[18]

Forrest N Iandola, Song Han, Matthew W Moskewicz, Khalid Ashraf, William J
Dally, and Kurt Keutzer. “SqueezeNet: AlexNet-Level Accuracy with 50x Fewer
Parameters and< 0.5 MB Model Size.” In: arXiv Preprint (2016). doi: 10 . 48550 /
arXiv.1602.07360.

[19] Tsung-Yi Lin, Michael Maire, Serge Belongie, James Hays, Pietro Perona, Deva
Ramanan, Piotr Dollár, and C Lawrence Zitnick. “Microsoft CoCo: Common Objects
in Context.” In: European Conference on Computer Vision. 2014, pp. 740–755. doi: 10.
48550/arXiv.1405.0312.
Joseph Redmon and Ali Farhadi. “YOLOv3: An Incremental Improvement.” In:
arXiv Preprint (2018). doi: 10.48550/arXiv.1804.02767.

[20]

[21] Ehsan Aghapour, Dolly Sapra, Andy Pimentel, and Anuj Pathania. “CPU-GPU
Layer-Switched Low Latency CNN Inference.” In: 25th Euromicro Conference on
Digital System Design. 2022, pp. 324–331. doi: 10.1109/DSD57027.2022.00051.

[22]

Shih-Chieh Lin, Yunqi Zhang, Chang-Hong Hsu, Matt Skach, Md E Haque, Lingjia
Tang, and Jason Mars. “The Architectural Implications of Autonomous Driving:
Constraints and Acceleration.” In: Proceedings of the 23rd Conference on Architectural
Support for Programming Languages and Operating Systems. 2018, pp. 751–766. doi:
10.1145/3173162.3173191.

bibliography

145

[23]

Jonatan S Dyrstad and John Reidar Mathiassen. “Grasping Virtual Fish: A Step
Towards Robotic Deep Learning from Demonstration in Virtual Reality.” In: IEEE
International Conference on Robotics and Biomimetics. 2017, pp. 1181–1187. doi: 10 .
1109/ROBIO.2017.8324578.

[24] Wei Liu, Dragomir Anguelov, Dumitru Erhan, Christian Szegedy, Scott Reed,
Cheng-Yang Fu, and Alexander C Berg. “SSD: Single Shot MultiBox Detector.” In:
European Conference on Computer Vision. 2016, pp. 21–37. doi: 10.1007/978- 3- 319-
46448-0_2.

[25] Tobias Pohlen, Alexander Hermans, Markus Mathias, and Bastian Leibe. “Full-
Resolution Residual Networks for Semantic Segmentation in Street Scenes.” In:
Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition. 2017,
pp. 4151–4160. doi: 10.48550/arXiv.1611.08323.

[26] Gopinath Mahale, Pramod Udupa, Kiran Kolar Chandrasekharan, and Sehwan Lee.
“WinDConv: A Fused Datapath CNN Accelerator for Power-Efficient Edge Devices.”
In: IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems 39.11
(2020), pp. 4278–4289. doi: 10.1109/TCAD.2020.3013096.

[27]

Siqi Wang, Anuj Pathania, and Tulika Mitra. “Neural Network Inference on Mobile
SOCs.” In: IEEE Design & Test 37.5 (2020), pp. 50–57. doi: 10 . 1109 / MDAT . 2020 .
2968258.

[28] Carole-Jean Wu, David Brooks, Kevin Chen, Douglas Chen, Sy Choudhury, Marat
Dukhan, Kim Hazelwood, Eldad Isaac, Yangqing Jia, Bill Jia, et al. “Machine
Learning at Facebook: Understanding Inference at the Edge.” In: IEEE International
Symposium on High Performance Computer Architecture. 2019, pp. 331–344. doi: 10 .
1109/HPCA.2019.00048.

[29]

Siqi Wang, Gayathri Ananthanarayanan, Yifan Zeng, Neeraj Goel, Anuj Pathania,
and Tulika Mitra. “High-Throughput CNN Inference on Embedded ARM big.
LITTLE Multicore Processors.” In: IEEE Transactions on Computer-Aided Design of
Integrated Circuits and Systems 39.10 (2019), pp. 2254–2267. doi: 10.1109/TCAD.2019.
2944584.

[30] Mark Sandler, Andrew Howard, Menglong Zhu, Andrey Zhmoginov, and Liang-
Chieh Chen. “MobileNetV2: Inverted Residuals and Linear Bottlenecks.” In: Pro-
ceedings of the IEEE Conference on Computer Vision and Pattern Recognition. 2018,
pp. 4510–4520. doi: 10.1109/CVPR.2018.00474.

[31] Matthieu Courbariaux, Itay Hubara, Daniel Soudry, Ran El-Yaniv, and Yoshua
Bengio. “Binarized Neural Networks: Training Deep Neural Networks with Weights
and Activations Constrained to +1 or -1.” In: arXiv Preprint (2016). doi: 10.48550/
arXiv.1602.02830.

[32] Caiwen Ding, Siyu Liao, Yanzhi Wang, Zhe Li, Ning Liu, Youwei Zhuo, Chao Wang,
Xuehai Qian, Yu Bai, Geng Yuan, et al. “CirCNN: Accelerating and Compressing
Deep Neural Networks Using Block-CirculantWeight Matrices.” In: Proceedings of the
50th Annual IEEE/ACM International Symposium on Microarchitecture. 2017, pp. 395–
408. doi: 10.1145/3123939.3124552.

[33]

Jiecao Yu, Andrew Lukefahr, David Palframan, Ganesh Dasika, Reetuparna Das, and
Scott Mahlke. “Scalpel: Customizing DNN Pruning to the Underlying Hardware
Parallelism.” In: ACM SIGARCH Computer Architecture News 45.2 (2017), pp. 548–560.
doi: 10.1145/3079856.3080215.

146

bibliography

[34] Yuan Meng, Sanmukh Kuppannagari, Rajgopal Kannan, and Viktor Prasanna. “DY-
NAMAP: Dynamic Algorithm Mapping Framework for Low Latency CNN Infer-
ence.” In: ACM/SIGDA International Symposium on Field-Programmable Gate Arrays.
2021, pp. 183–193. doi: 10.1145/3431920.3439286.

[35] Zhaoying Li, Dhananjaya Wijerathne, Xianzhang Chen, Anuj Pathania, and Tulika
Mitra. “ChordMap: Automated Mapping of Streaming Applications Onto CGRA.”
In: IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems
(2021). doi: 10.1109/TCAD.2021.3058313.

[36] Dhananjaya Wijerathne, Zhaoying Li, Anuj Pathania, Tulika Mitra, and Lothar
Thiele. “HiMap: Fast and Scalable High-Quality Mapping on CGRA via Hierarchical
Abstraction.” In: IEEE Transactions on Computer-Aided Design of Integrated Circuits and
Systems (2021). doi: 10.1109/TCAD.2021.3132551.

[37]

Svetlana Minakova, Erqian Tang, and Todor Stefanov. “Combining Task-and Data-
Level Parallelism for High-Throughput CNN Inference on Embedded CPUs-GPUs
MPSoCs.” In: International Conference on Embedded Computer Systems. 2020, pp. 18–35.
doi: 10.1007/978-3-030-60939-9_2.

[38] Myeonggyun Han, Jihoon Hyun, Seongbeom Park, Jinsu Park, and Woongki Baek.
“MOSAIC: Heterogeneity-, Communication-, and Constraint-Aware Model Slicing
and Execution for Accurate and Efficient Inference.” In: 28th International Conference
on Parallel Architectures and Compilation Techniques. 2019, pp. 165–177. doi: 10.1109/
PACT.2019.00021.

[39] Loc N Huynh, Youngki Lee, and Rajesh Krishna Balan. “DeepMon: Mobile GPU-
based Deep Learning Framework for Continuous Vision Applications.” In: Proceed-
ings of the 15th Annual International Conference on Mobile Systems, Applications, and
Services. 2017, pp. 82–95. doi: 10.1145/3081333.3081360.

[40] Youngsok Kim, Joonsung Kim, Dongju Chae, Daehyun Kim, and Jangwoo Kim.
“µLayer: Low Latency On-Device Inference Using Cooperative Single-Layer Acceler-
ation and Processor-Friendly Quantization.” In: Proceedings of the Fourteenth EuroSys
Conference 2019. 2019, pp. 1–15. doi: 10.1145/3302424.3303950.

[41] Nicholas D Lane, Sourav Bhattacharya, Petko Georgiev, Claudio Forlivesi, Lei Jiao,
Lorena Qendro, and Fahim Kawsar. “DeepX: A Software Accelerator for Low-
Power Deep Learning Inference on Mobile Devices.” In: 15th ACM/IEEE International
Conference on Information Processing in Sensor Networks. 2016, pp. 1–12. doi: 10.1109/
IPSN.2016.7460664.

[42] Woosung Kang, Kilho Lee,

Insik Shin, and Hoon Sung Chwa.
“LaLaRAND: Flexible Layer-by-Layer CPU/GPU Scheduling for Real-Time DNN
Tasks.” In: 2021 IEEE Real-Time Systems Symposium. 2021, pp. 329–341. doi: 10.1109/
RTSS52674.2021.00038.

Jinkyu Lee,

[43] Duseok Kang, Jinwoo Oh, Jongwoo Choi, Youngmin Yi, and Soonhoi Ha. “Schedul-
ing of Deep Learning Applications Onto Heterogeneous Processors in an Embedded
Device.” In: IEEE Access 8 (2020), pp. 43980–43991. doi: 10 . 1109 / ACCESS . 2020 .
2977496.

[44]

Seonyeong Heo, Sungjun Cho, Youngsok Kim, and Hanjun Kim. “Real-Time Ob-
ject Detection System with Multi-Path Neural Networks.” In: IEEE Real-Time and
Embedded Technology and Applications Symposium. 2020, pp. 174–187. doi: 10 . 1109 /
RTAS48715.2020.000-8.

bibliography

147

[45] Ehsan Aghapour, Dolly Sapra, Andy D Pimentel, and Anuj Pathania. “PELSI:
Power-Efficient Layer-Switched Inference.” In: IEEE 29th International Conference on
Embedded and Real-Time Computing Systems and Applications. 2023, pp. 12–17. doi:
10.1109/RTCSA58653.2023.00011.

[46] Anuj Pathania, Qing Jiao, Alok Prakash, and Tulika Mitra. “Integrated CPU-GPU
Power Management for 3D Mobile Games.” In: 51st ACM/EDAC/IEEE Design Au-
tomation Conference. 2014, pp. 1–6. doi: 10.1145/2593069.2593151.

[47] Anuj Pathania, Alexandru Eugen Irimiea, Alok Prakash, and Tulika Mitra. “Power-
Performance Modelling of Mobile Gaming Workloads on Heterogeneous MPSoCs.”
In: Proceedings of the 52nd Annual Design Automation Conference. 2015, pp. 1–6. doi:
10.1145/2744769.2744894.

[48] Luca Cremona, William Fornaciari, and Davide Zoni. “Automatic Identification and
Hardware Implementation of a Resource-Constrained Power Model for Embedded
Systems.” In: Sustainable Computing: Informatics and Systems 29 (2021). doi: 10.1016/
j.suscom.2020.100467.

[49] Ganapati Bhat, Sumit K Mandal, Sai T Manchukonda, Sai V Vadlamudi, Ayushi
Agarwal, Jun Wang, and Umit Y Ogras. “Per-Core Power Modeling for Heteroge-
nous SoCs.” In: MDPI Electronics 10.19 (2021). doi: 10.3390/electronics10192428.
[50] Hyochan An, Sam Schiferl, Siddharth Venkatesan, Tim Wesley, Qirui Zhang,
Jingcheng Wang, Kyojin D Choo, Shiyu Liu, Bowen Liu, Ziyun Li, et al. “An Ultra-
Low-Power Image Signal Processor for Hierarchical Image Recognition With Deep
Neural Networks.” In: IEEE Journal of Solid-State Circuits 56.4 (2020), pp. 1071–1081.
doi: 10.1109/JSSC.2020.3041858.

[51] Yigit Tuncel, Sizhe An, Ganapati Bhat, Naga Raja, Hyung Gyu Lee, and Umit Ogras.
“Voltage-Frequency Domain Optimization for Energy-Neutral Wearable Health De-
vices.” In: MDPI Sensors 20.18 (2020). doi: 10.3390/s20185255.

[52] TaiYu Cheng, Jaehoon Yu, and Masanori Hashimoto. “Minimizing Power for Neural
Network Training with Logarithm-Approximate Floating-Point Multiplier.” In: 29th
International Symposium on Power and Timing Modeling, Optimization and Simulation.
2019, pp. 91–96. doi: 10.1109/PATMOS.2019.8862162.

[53] Ali HeydariGorji, Mahdi Torabzadehkashi, Siavash Rezaei, Hossein Bobarshad,
Vladimir Alves, and Pai H Chou. “Stannis: Low-Power Acceleration of DNN Train-
ing Using Computational Storage Devices.” In: 57th ACM/IEEE Design Automation
Conference. 2020, pp. 1–6. doi: 10.1109/DAC18072.2020.9218687.

[54]

Svetlana Minakova, Dolly Sapra, Todor Stefanov, and Andy D Pimentel. “Scenario
Based Run-Time Switching for Adaptive CNN-Based Applications at the Edge.” In:
ACM Transactions on Embedded Computing Systems 21.2 (2022), pp. 1–33. doi: 10.1145/
3488718.

[55] Zhenheng Tang, Yuxin Wang, Qiang Wang, and Xiaowen Chu. “The Impact of GPU
DVFS on the Energy and Performance of Deep Learning: an Empirical Study.” In:
Proceedings of the Tenth ACM International Conference on Future Energy Systems. 2019.
doi: 10.1145/3307772.3328315.

[56]

Junyeol Yu, Jongseok Kim, and Euiseong Seo. “A DNN Inference Latency-Aware
GPU Power Management Scheme.” In: IEEE 3rd Eurasia Conference on IOT, Commu-
nication and Engineering. 2021. doi: 10.1109/ECICE52819.2021.9645654.

148

bibliography

[57] Xiaotian Guo, Andy D. Pimentel, and Todor Stefanov. “Automated Exploration and
Implementation of Distributed CNN Inference at the Edge.” In: IEEE Internet of
Things Journal 10.7 (2023), pp. 5843–5858. doi: 10.1109/JIOT.2023.3237572.
[58] Yuyang Sun, Zhixin Ou, Juan Chen, Xinxin Qi, Yifei Guo, Shunzhe Cai, and Xiaom-
ing Yan. “Evaluating Performance, Power and Energy of Deep Neural Networks on
CPUs and GPUs.” In: 39th National Conference of Theoretical Computer Science. 2021.
doi: 10.1007/978-981-16-7443-3_12.

[59] Zhixin Ou, Juan Chen, Yuyang Sun, Tao Xu, Guodong Jiang, Zhengyuan Tan, and
Xinxin Qi. “AOA: Adaptive Overclocking Algorithm on CPU-GPU Heterogeneous
Platforms.” In: International Conference on Algorithms and Architectures for Parallel
Processing. 2022, pp. 253–272. doi: 10.1007/978-3-031-22677-9_14.

[60] Ehsan Aghapour, Yixian Shen, Dolly Sapra, Andy Pimentel, and Anuj Pathania.
“PiQi: Partially Quantized DNN Inference on HMPSoCs.” In: Proceedings of the 29th
ACM/IEEE International Symposium on Low Power Electronics and Design. 2024, pp. 1–6.
doi: 10.1145/3665314.3670841.

[61] Ramyad Hadidi, Jiashen Cao, Yilun Xie, Bahar Asgari, Tushar Krishna, and Hyesoon
Kim. “Characterizing the Deployment of Deep Neural Networks on Commercial
Edge Devices.” In: IEEE International Symposium on Workload Characterization. 2019.
doi: 10.1109/IISWC47752.2019.9041955.

[62] Andreas Karatzas and Iraklis Anagnostopoulos. “OmniBoost: Boosting Throughput
of Heterogeneous Embedded Devices under Multi-DNN Workload.” In: 2023 60th
ACM/IEEE Design Automation Conference. 2023, pp. 1–6. doi: 10.1109/DAC56929.2023.
10247989.

[63] Kyuho J. Lee. “Architecture of Neural Processing Unit for Deep Neural Networks.”
In: Hardware Accelerator Systems for Artificial Intelligence and Machine Learning. Ad-
vances in Computers. Elsevier, 2021. doi: https : / / doi . org / 10 . 1016 / bs . adcom .
2020.11.001.

[64] Ehsan Aghapour, Dolly Sapra, Andy Pimentel, and Anuj Pathania. “ARM-CO-
UP: ARM COoperative Utilization of Processors.” In: ACM Transactions on Design
Automation of Electronic Systems (2024). doi: 10.1145/3656472.

[65] Markus Nagel, Marios Fournarakis, Rana Ali Amjad, Yelysei Bondarenko, Mart van
Baalen, and Tijmen Blankevoort. “A White Paper on Neural Network Quantization.”
In: arXiv Preprint (2021). doi: 10.48550/arXiv.2106.08295.

[66] Markus Nagel, Mart van Baalen, Tijmen Blankevoort, and Max Welling. “Data-Free
Quantization Through Weight Equalization and Bias Correction.” In: Proceedings of
the IEEE/CVF International Conference on Computer Vision. 2019. doi: 10.48550/arXiv.
1906.04721.

[67] Yuhang Li, Ruihao Gong, Xu Tan, Yang Yang, Peng Hu, Qi Zhang, Fengwei Yu, Wei
Wang, and Shi Gu. “BRECQ: Pushing the Limit of Post-Training Quantization by
Block Reconstruction.” In: arXiv Preprint (2021). doi: 10.48550/arXiv.2102.05426.

[68] Hokchhay Tann, Soheil Hashemi, R. Iris Bahar, and Sherief Reda. “Hardware-
Software Codesign of Accurate, Multiplier-Free Deep Neural Networks.” In: Pro-
ceedings of the 54th Annual Design Automation Conference. 2017. doi: 10.1145/3061639.
3062259.

bibliography

149

[69]

[70]

Peisong Wang, Weihan Chen, Xiangyu He, Qiang Chen, Qingshan Liu, and Jian
Cheng. “Optimization-Based Post-Training Quantization With Bit-Split and Stitch-
ing.” In: IEEE Transactions on Pattern Analysis and Machine Intelligence (2023). doi:
10.1109/TPAMI.2022.3159369.

Shubham Jain, Swagath Venkataramani, Vijayalakshmi Srinivasan, Jungwook Choi,
Pierce Chuang, and Leland Chang. “Compensated-DNN: Energy Efficient Low-
Precision Deep Neural Networks by Compensating Quantization Errors.” In: Pro-
ceedings of the 55th Annual Design Automation Conference. 2018. doi: 10.1145/3195970.
3196012.

[71] Hyunho Ahn, Tian Chen, Nawras Alnaasan, Aamir Shafi, Mustafa Abduljabbar,
Hari Subramoni, Dhabaleswar K., and Panda. “Performance Characterization of
using Quantization for DNN Inference on Edge Devices: Extended Version.” In:
arXiv Preprint (2023). doi: 10.48550/arXiv.2303.05016.

[72] Claudionor N. Coelho, Aki Kuusela, Shan Li, Hao Zhuang, Jennifer Ngadiuba,
Thea Klaeboe Aarrestad, Vladimir Loncar, Maurizio Pierini, Adrian Alan Pol, and
Sioni Summers. “Automatic Heterogeneous Quantization of Deep Neural Networks
for Low-Latency Inference on the Edge for Particle Detectors.” In: Nature Machine
Intelligence (2021). doi: 10.1038/s42256-021-00356-5.

[73]

[74]

Satoki Tsuji, Fuyuka Yamada, Hiroshi Kawaguchi, Atsuki Inoue, and Yasufumi Sakai.
“Greedy Search Algorithm for Partial Quantization of Convolutional Neural Net-
works Inspired by Submodular Optimization.” In: Neural Computing and Applications
(2022). doi: 10.1007/s00521-021-06752-7.

Jie Tang, Dawei Sun, Shaoshan Liu, and Jean-Luc Gaudiot. “Enabling Deep Learning
on IoT Devices.” In: IEEE Computer 50.10 (2017), pp. 92–96. doi: 10.1109/MC.2017.
3641648.

[75] Deb Kalyanmoy. “A Fast and Elitist Multi-Objective Genetic Algorithm: NSGA-II.”
In: IEEE Transactions on Evolutionary Computation (2002). doi: 10.1109/4235.996017.
[76] Ehsan Aghapour, Yujie Zhang, Anuj Pathania, and Tulika Mitra. “Pipelined CNN
Inference on Heterogeneous Multi-processor System-on-Chip.” In: Embedded Ma-
chine Learning for Cyber-Physical, IoT, and Edge Computing: Software Optimizations and
Hardware/Software Codesign. 2023, pp. 405–427. doi: 10 . 1007 / 978 - 3 - 031 - 39932 -
9_16.

[77] Ehsan Aghapour, A Pathania, and Gayathri Ananthanarayanan. “Integrated ARM
big.LITTLE-Mali Pipeline for High-Throughput CNN Inference.” In: Authorea
Preprints (2023). doi: 10.36227/techrxiv.14994885.v2.

[78] Anuj Pathania, Santiago Pagani, Muhammad Shafique, and Jörg Henkel. “Power
Management for Mobile Games on Asymmetric Multi-Cores.” In: IEEE/ACM In-
ternational Symposium on Low Power Electronics and Design. 2015, pp. 243–248. doi:
10.1109/ISLPED.2015.7273521.

[79]

Pirah Noor Soomro, Mustafa Abduljabbar, Jeronimo Castrillon, and Miquel Pericàs.
“An Online Guided Tuning Approach to Run CNN Pipelines on Edge Devices.”
In: Proceedings of the 18th ACM International Conference on Computing Frontiers. 2021,
pp. 45–53. doi: 10.1145/3457388.3458662.

150

bibliography

[80] Hsin-I Wu, Da-Yi Guo, Hsu-Hsun Chin, and Ren-Song Tsay. “A Pipeline-Based
Scheduler for Optimizing Latency of Convolution Neural Network Inference over
Heterogeneous Multicore Systems.” In: 2nd IEEE International Conference on Artificial
Intelligence Circuits and Systems. 2020, pp. 46–49. doi: 10 . 1109 / AICAS48895 . 2020 .
9073977.

[81] Bogil Kim, Sungjae Lee, Amit Ranjan Trivedi, and William J Song. “Energy-Efficient
Acceleration of Deep Neural Networks on Realtime-Constrained Embedded Edge
Devices.” In: IEEE Access 8 (2020), pp. 216259–216270. doi: 10.1109/ACCESS.2020.
3038908.

[82] Eun Jin Jeong, Jangryul Kim, Samnieng Tan, Jaeseong Lee, and Soonhoi Ha. “Deep
Learning Inference Parallelization on Heterogeneous Processors with TensorRT.” In:
IEEE Embedded Systems Letters (2021). doi: 10.1109/LES.2021.3087707.

[83] EunJin Jeong, Jangryul Kim, and Soonhoi Ha. “TensorRT-Based Framework and
Optimization Methodology for Deep Learning Inference on Jetson Boards.” In: ACM
Transactions on Embedded Computing Systems (2022). doi: 10.1145/3508391.

[84]

Ismet Dagli, Alexander Cieslewicz, Jedidiah McClurg, and Mehmet E Belviranli.
“AxoNN: Eenergy-Aware Execution of Neural Network Inference on Multi-
Accelerator Heterogeneous SoCs.” In: Proceedings of the 59th ACM/IEEE Design
Automation Conference. 2022, pp. 1069–1074. doi: 10.1145/3489517.3530572.
[85] Tyrone Tai-On Kwok and Yu-Kwong Kwok. “On the Design, Control, and Use of a
Reconfigurable Heterogeneous Multi-Core System-on-a-Chip.” In: IEEE International
Symposium on Parallel and Distributed Processing. 2008, pp. 1–11. doi: 10.1109/IPDPS.
2008.4536165.

[86]

[87]

Jessie Y. C. Chen and Jennifer E. Thropp. “Review of Low Frame Rate Effects on
Human Performance.” In: IEEE Transactions on Systems, Man, and Cybernetics - Part
A: Systems and Humans 37.6 (2007), pp. 1063–1076. doi: 10.1109/TSMCA.2007.904779.

Jussi Hanhirova, Teemu Kämäräinen, Sipi Seppälä, Matti Siekkinen, Vesa Hirvisalo,
and Antti Ylä-Jääski. “Latency and Throughput Characterization of Convolutional
Neural Networks for Mobile Computer Vision.” In: Proceedings of the 9th ACM
Multimedia Systems Conference. 2018, 204–215. doi: 10.1145/3204949.3204975. url:
https://doi.org/10.1145/3204949.3204975.

[88] Alexander Hoffman, Anuj Pathania, Philipp H. Kindt, Samarjit Chakraborty, and
Tulika Mitra. “BrezeFlow: Unified Debugger for Android CPU Power Governors and
Schedulers on Edge Devices.” In: 2020 57th ACM/IEEE Design Automation Conference.
2020, pp. 1–6. doi: 10.1109/DAC18072.2020.9218542.

[89] Mingwen Shao, Junhui Dai, Jiandong Kuang, and Deyu Meng. “A Dynamic CNN
Pruning Method Based on Matrix Similarity.” In: Signal, Image and Video Processing
15.2 (2021), pp. 381–389. doi: 10.1007/s11760-020-01760-x.

[90]

Sean Young, Zhe Wang, David Taubman, and Bernd Girod. “Transform Quantiza-
tion for CNN Compression.” In: IEEE Transactions on Pattern Analysis and Machine
Intelligence (2021). doi: 10.1109/TPAMI.2021.3084839.

[91] Xiangzhong Luo, Di Liu, Shuo Huai, Hao Kong, Hui Chen, and Weichen Liu.
“Designing Efficient DNNs via Hardware-Aware Neural Architecture Search and
Beyond.” In: IEEE Transactions on Computer-Aided Design of Integrated Circuits and
Systems 41.6 (2021), pp. 1799–1812. doi: 10.1109/TCAD.2021.3100249.

bibliography

151

[92] Dolly Sapra and Andy D Pimentel. “Constrained Evolutionary Piecemeal Training
to Design Convolutional Neural Networks.” In: Trends in Artificial Intelligence Theory
and Applications. 2020, pp. 709–721. doi: 10.1007/s10489-021-02679-7.

[93] Tianqi Chen, Thierry Moreau, Ziheng Jiang, Lianmin Zheng, Eddie Yan, Haichen
Shen, Meghan Cowan, Leyuan Wang, Yuwei Hu, Luis Ceze, et al. “TVM: An
Automated End-to-End Optimizing Compiler for Deep Learning.” In: 13th USENIX
Symposium on Operating Systems Design and Implementation. 2018, pp. 578–594. doi:
10.48550/arXiv.1802.04799.

[94] Dawei Sun, Shaoshan Liu, and Jean-Luc Gaudiot. “Enabling Embedded Inference
Engine with ARM compute Library: A Case Study.” In: arXiv Preprint (2017). doi:
10.48550/arXiv.1704.04861.

[95] Hung-Yang Chang, Seyyed Hasan Mozafari, Cheng Chen, James J. Clark, Brett H.
Meyer, and Warren J. Gross. “PipeBERT: High-throughput BERT Inference for ARM
big.LITTLE Multi-core Processors.” In: Journal of Signal Processing Systems 95.7 (2023),
pp. 877–894. issn: 1939-8115. doi: 10.1007/s11265-022-01814-y.

[96] Wonik Seo, Sanghoon Cha, Yeonjae Kim, Jaehyuk Huh, and Jongse Park. “SLO-
Aware Inference Scheduler for Heterogeneous Processors in Edge Platforms.” In:
ACM Transactions on Architecture and Code Optimization 18.4 (2021), pp. 1–26. doi:
10.1145/3460352.

[97] Don W. Wijerathne, Zihao Li, Madhura Karunarathne, Anuj Pathania, and Tulika Mi-
tra. “CASCADE: High Throughput Data Streaming via Decoupled Access-Execute
CGRA.” In: ACM Transactions on Embedded Computing Systems 18.5s (2019), pp. 1–26.
doi: 10.1145/3358177.

[98]

Junzhong Shen, You Huang, Zelong Wang, Yuran Qiao, Mei Wen, and Chunyuan
Zhang. “Towards a Uniform Template-Based Architecture for Accelerating 2D and
3D CNNs on FPGA.” In: International Symposium on Field-Programmable Gate Arrays.
New York, NY, USA: Association for Computing Machinery, 2018, 97–106. doi: 10.
1145/3174243.3174257.

[99] Di Wu, Yu Zhang, Xijie Jia, Lu Tian, Tianping Li, Lingzhi Sui, Dongliang Xie, and
Yi Shan. “A High-Performance CNN Processor Based on FPGA for MobileNets.” In:
2019 29th International Conference on Field Programmable Logic and Applications (FPL).
2019, pp. 136–143. doi: 10.1109/FPL.2019.00030.

[100] Thannirmalai Somu Muthukaruppan, Anuj Pathania, and Tulika Mitra. “Price The-
ory Based Power Management for Heterogeneous Multi-Cores.” In: ACM SIGPLAN
Notices 49.4 (2014), pp. 161–176. doi: 10.1145/2541940.2541974.

"A short quote, originally by."

— name of the quote author

A C K N O W L E D G M E N T S

kgl kujdfsg dgsd gds g

153

S U M M A R Y

DL has become a cornerstone technology across various domains, offering
superior performance in tasks like image classification, speech analysis, and
natural language processing. While these models often rely on powerful
servers or the cloud for heavy computations, there is a growing demand to
run them locally on end devices—reducing latency and enhancing privacy.
Modern end devices integrate HMPSoCs that combine CPUs, GPUs,
and sometimes NPUs. These architectures open new opportunities for on-
device DL but introduce tight power, memory, and real-time responsiveness
constraints. Balancing these constraints requires careful optimizations that
effectively exploit different hardware units.

A central strategy is layer-wise switching, which assigns individual
neural network layers to CPUs or GPUs depending on their resource needs.
Although switching incurs some overhead, experimental results show that
it consistently lowers end-to-end inference latency, making it valuable for
applications like augmented reality and autonomous systems, where every
millisecond saved is critical.

Building on layer-wise switching, DVFS addresses power concerns. By
selectively tuning the frequency of CPU or GPU cores at the granularity
of each layer, the system can save energy without violating strict latency
requirements. Profiling data identifies layers that benefit from higher fre-
quencies, while others can safely operate at lower clock rates, yielding
significant power reductions in real devices.

Specialized hardware like NPUs further raises efficiency but may require
reduced numerical precision. To mitigate potential accuracy drops, a partial
quantization approach designates only certain layers for NPU execution.
This preserves vital accuracy in key layers on CPU or GPU while leveraging
the NPU’s high performance and low power draw. Careful selection of
which layers to quantize ensures that model accuracy remains acceptable
for demanding applications.

For real-time tasks that demand high throughput (e.g., video analytics),
the thesis investigates pipeline-based scheduling, splitting networks into
segments that run concurrently across different processors. By overlapping

155

156

summary

computations for multiple frames, pipeline execution boosts FPS and often
lowers energy costs per frame, as hardware resources remain occupied
rather than cycling between idle and active states.

These methods—layer switching, DVFS, partial quantization, and pipelin-
ing—are unified in an open-source framework that automates device assign-
ment, profiling, and quantization process. By supporting CPUs, GPUs, and
NPUs collectively, it greatly reduces the complexity of deploying advanced
neural networks on embedded platforms. Comprehensive experiments con-
firm that such coordinated strategies enhance both performance and power
efficiency, enabling on-device ML even under stringent resource limitations.
Ultimately, this thesis demonstrates how an integrated approach to
scheduling, hardware tuning, and quantization can unlock the full potential
of AI on end devices. These optimizations enable local data processing, safe-
guard sensitive information, and reduce network reliance—core advantages
in domains ranging from mobile applications to healthcare and industrial
automation. The methods and tools developed thus serve as both a practical
guide and a stepping stone for future research on efficient neural inference
at the end devices.

S A M E N VAT T I N G

Deep learning (DL) is uitgegroeid tot een fundamentele technologie in tal
van domeinen en biedt superieure prestaties bij taken zoals beeldclassifi-
catie, spraakanalyse en natural language processing. Hoewel deze modellen
vaak vertrouwen op krachtige servers of de cloud voor zware berekeningen,
bestaat er een groeiende vraag om ze lokaal op eindapparaten te draaien,
waardoor de latentie daalt en de privacy toeneemt.

Moderne eindapparaten, zoals smartphones en tablets, bevatten het-
erogene multi-processing system-on-chips (HMPSoC’s) die CPU’s, GPU’s
en soms neural processing units (NPU’s) combineren. Deze architecturen
bieden nieuwe kansen voor deep learning op het apparaat zelf, maar
brengen ook strenge beperkingen met zich mee op het gebied van energie,
geheugen en real-time reactiesnelheid. Om deze beperkingen in balans te
brengen, zijn doordachte optimalisaties nodig die de beschikbare hardware
effectief benutten.

Een belangrijke benadering is “laag-voor-laag schakelen,” waarbij in-
dividuele lagen van een neuraal netwerk aan CPU’s of GPU’s worden
toegewezen, afhankelijk van hun resourcebehoeften. Hoewel het schakelen
een zekere overhead met zich meebrengt, tonen experimentele resultaten
aan dat de totale inferentietijd consequent wordt verlaagd. Dit is met
name waardevol voor toepassingen zoals augmented reality en autonome
systemen, waarin elke milliseconde telt.

Bovenop deze laag-voor-laag schakeling behandelt Dynamic Voltage and
Frequency Scaling (DVFS) de energieproblematiek. Door de frequentie van
CPU- en GPU-cores selectief af te stemmen op het detailniveau van elke
laag, kan het systeem energie besparen zonder strikte latentie-eisen te
schenden. Uit profieldata blijkt welke lagen profiteren van hogere frequen-
ties en welke veilig op lagere klokniveaus kunnen draaien, wat aanzienlijke
energiebesparingen oplevert op echte apparaten.

Gespecialiseerde hardware zoals NPU’s biedt verder verhoogde efficiën-
tie, maar kan gereduceerde numerieke precisie vereisen. Om mogelijke
nauwkeurigheidsverliezen te beperken, voorziet een aanpak van gedeel-
telijke kwantisering alleen bepaalde lagen voor NPU-uitvoering. Zo blijft de

157

158

samenvatting

essentiële nauwkeurigheid van cruciale lagen op de CPU of GPU behouden,
terwijl de hoge prestaties en het lage energieverbruik van de NPU optimaal
worden benut. Een zorgvuldige selectie van te kwantiseren lagen waarborgt
dat de modelnauwkeurigheid geschikt blijft voor veeleisende toepassingen.
Voor real-time taken die een hoge verwerkingssnelheid vereisen (zoals
videoanalyse), onderzoekt de thesis een pijplijnschema waarmee netwerken
in segmenten worden opgesplitst die parallel op verschillende processoren
draaien. Door berekeningen voor meerdere frames te overlappen, vergroot
de pijplijnuitvoering het aantal frames per seconde en verlaagt het vaak de
energiekosten per frame, omdat hardware continu wordt benut in plaats
van afwisselend actief en inactief te zijn.

Deze methoden—laag-voor-laag schakelen, DVFS, gedeeltelijke kwan-
tisering en pijplijnverwerking—worden samengebracht
in een open-
sourceraamwerk dat de apparaattoewijzing, profiling en kwantisatieau-
tomatiseert. Door CPU’s, GPU’s en NPU’s gezamenlijk te ondersteunen,
wordt de complexiteit van het
inzetten van geavanceerde neurale
netwerken op embedded platforms aanzienlijk verminderd. Uitgebreide
experimenten bevestigen dat zulke gecoördineerde strategieën zowel de
prestaties als de energie-efficiëntie verbeteren, waardoor on-device ML
zelfs onder strikte beperkingen mogelijk wordt.

Al met al toont deze thesis aan hoe een geïntegreerde aanpak van
planning, hardware-afstemming en kwantisatie het volledige potentieel
van embedded AI kan ontsluiten. Deze optimalisaties maken lokale
gegevensverwerking mogelijk, beschermen gevoelige informatie en vermin-
deren de afhankelijkheid van netwerkverbindingen—essentiële voordelen
in sectoren variërend van mobiele toepassingen tot gezondheidszorg en
industriële automatisering. De ontwikkelde methoden en hulpmiddelen
fungeren daarbij zowel als praktische leidraad als als opstap voor
toekomstig onderzoek naar efficiënte neurale inferentie op eindapparaten.

