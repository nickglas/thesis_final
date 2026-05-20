Cheetah: Lean and Fast Secure Two-Party Deep Neural Network Inference
ZhicongHuang Wen-jieLu ChengHong JianshengDing
AlibabaGroup AlibabaGroup AlibabaGroup AlibabaGroup
Abstract learntheinferenceresultF(x)butnothingelsebeyondwhat
canbederivedfromF(x).Apossibleapplicationisprivacy-
Securetwo-partyneuralnetworkinference(2PC-NN)can
preservingfacerecognition,wheretheservercouldidentify
offerprivacyprotectionforboththeclientandtheserverand
criminalsfromphotoswithoutviewingthephotocontents.
isapromisingtechniqueinthemachine-learning-as-a-service
Unfortunately,therestillexistperformancegapsbetween
setting.However,thelargeoverheadofthecurrent2PC-NNin-
thecurrent2PC-NNinferencesystemsandreal-worldapplica-
ferencesystemsisstillbeingaheadache,especiallywhenap-
tions.Becauseoflargecomputationandcommunicationover-
pliedtodeepneuralnetworkssuchasResNet50.Inthiswork,
head,thosesystemshavebeenlimitedtosmalldatasets(such
wepresentCheetah,anew2PC-NNinferencesystemthatis
asMNISTandCIFAR)orsimplemodels(e.g.withafewhun-
fasterandmorecommunication-efficientthanstate-of-the-arts.
dredsofparameters).RecentlythesystemCrypTFlow2[46]
ThemaincontributionsofCheetaharetwo-fold:thefirstpart
hasmadeconsiderableimprovements,anddemonstrate,for
includescarefullydesignedhomomorphicencryption-based
the first time, the ability to perform 2PC-NN inference at
protocolsthatcanevaluatethelinearlayers(namelyconvo-
thescaleofImageNet.Despitetheiradvances,thereremains
lution, batch normalization, and fully-connection) without
considerableoverhead:Forinstance,usingCrypTFlow2,the
anyexpensiverotationoperation.Thesecondpartincludes
serverandtheclientmightneedmorethan15minutestorun
severalleanandcommunication-efficientprimitivesforthe
andexchangemorethan30gigabytesofmessagestoperform
non-linearfunctions(e.g.,ReLUandtruncation).UsingChee-
onesecureinferenceonResNet50.
tah,wepresentintensivebenchmarksoverseverallarge-scale
Ourcontribution.Inthispaper,wepresentCheetah1,ase-
deepneuralnetworks.TakeResNet50foranexample,anend-
cureandfasttwo-partyinferencesystemfordeepneuralnet-
to-endexecutionofCheetahunderaWANsettingcostsless
works(DNN).Cheetahachievesitsperformanceviaacareful
than2.5minutesand2.3gigabytesofcommunication,which
co-design ofDNN,lattice-basedhomomorphicencryption,
outperformsCrypTFlow2(ACMCCS2020)byabout5.6×
oblivioustransfer,andsecret-sharing.Cheetahcontributesa
and12.9×,respectively.
setofnovelcryptographic protocols forthe mostcommon
linearoperationsandnon-linearoperationsofDNNs.Cheetah
1 Introduction canperformsecureinferenceonlargemodels,e.g.ResNet,
andDenseNet[28],withsignificantlysmallercomputation
andcommunicationoverheadsthanthestate-of-the-art2PC-
Toalleviatesomeoftheprivacyconcernsassociatedwiththe
NNinferencesystems.Forinstance,usingCheetah,theserver
ubiquitousdeploymentofdeeplearningtechnologies,many
andtheclientcanperformonesecureinferenceonResNet50
works[2,6,10,17,21,34,39,41]inthepastfewyearshave
within 2.5 minutes,exchanging less than 2.3 gigabytes of
introducedcryptographicframeworksbasedonsecuretwo-
messagesunderawideareanetworksetting,whichimproves
party computation (2PC) [5] to enable privacy-preserving
overCrypTFlow2byabout5.6×and12.9×,respectively.
(deep)neuralnetworkinference.Theproblemtheyaretry-
PotentialRealWorldApplications.In[57],theresearchers
ingtosolvecouldbedescribedasfollows:Aserverholdsa
trainaDenseNet121topredictlungdiseasesfromchestX-
valuablepre-trainedneuralnetworkmodelF.Theserveris
ray images.Also, [24] uses DNNs for diagnosing Diabetic
willingtoprovideF asaservicebutdoesnotwanttogiveout
Retinopathy(oneofthemajorcausesofblindness)fromreti-
Fdirectly.AclientwantstouseFtopredictonherdatax,but
nalimages.Asuchpredictioncanbedonesecurelywithin3
sheconsidersxasprivateinformationanddoesnotwantto
revealittotheserver.2PCprotocolscouldsolvethisdilemma 1Our implementation is available from https://github.com/
andfulfillbothparties’requirements:Theparticipant(s)could Alibaba-Gemini-Lab/OpenCheetah

minuteswithCheetah. and SIMD-tailored protocols [6,7,10,21,34] to rotate the
operandsmanytimes.Notethattherotationisanexpensive
operationevencomparedtothemultiplicationintherealmof
1.1 OurTechniques
HE,e.g.,30×moreexpensivecf.[6,Table9].Thesemassive
The layers of modern DNNs consist of alternating linear homomorphicrotationshavebecomeamajorobstacletothe
and non-linear operations. To design efficient 2PC-NN in- existing2PC-NNinferencesystems.
ferencesystems,multipletypesofcryptographicprimitives Asacomparison,theHE-basedprotocolsinCheetahare
arecommonlyusedtogether.Forinstance,DELPHI[41]and freeofhomomorphicrotation.Wepresentthreepairsofen-
CrypTFlow2 [46] leverage homomorphic encryption (HE)
codingfunctions(πi ,πw)thatenableustoevaluatethelinear
F F
toevaluatethelinearfunctionsofDNNandturntogarbled layersF∈{CONV,BN,FC}ofDNNsviapolynomialarith-
circuits(GC)oroblivioustransfer(OT)tocomputethenon- meticcircuits.Theseencodingfunctionsmapthevaluesof
linear functions of DNN. Cheetah is also a hybrid system theinput(e.g.,tensororvector)tothepropercoefficientsof
withnovelinsightsondesigningthebaseprotocolsandon theoutputpolynomial(s).Bycarefuldesignofthecoefficient
thewayhowtocoordinatedifferenttypesofcryptographic mappings,wenotonlyeliminatetheexpensiverotationsbut
primitives. We describe a high-leveloverview ofourmain arealsoabletoacceptsecretsharesfromZ 2(cid:96) forfree.For
techniquesfromthreeaspects. example, the secure convolution HomCONV(T,K) (given
laterin Figure 4) in Cheetahcouldbe computedvia justa
singlehomomorphicmultiplicationbetweentwopolynomi-
1.1.1 AchievingtheBestinTwoWorlds alstˆand kˆ wheretˆ=πi (T) is the encoded tensorand
CONV
Most of the existing 2PC-NN systems [39,41,43,46] sug- kˆ=πw (K)istheencodedkernel,respectively.
CONV
gest using the additive secret sharing technique to switch Interestingly,ournewdesignalsohelpstoreducethecost
back-and-forthbetweendifferenttypesofcryptographicprim- of otherhomomorphic operations (e.g.,encryption and de-
itives. Thereremainsaquestionthatwhichdomainshould cryption). On one hand,the rotation-basedapproaches use
beusedfortheadditivesharing,aprimefieldZ orthering alargelatticedimensione.g.,N≥8192.Ontheotherhand,
p
Z ?Asshownin[46],forthenon-linearfunctionsofDNNs, Cheetahcanuseasmallerdimension(i.e.,N=4096)tooffer
2(cid:96)
OT-basedprotocolsontheringZ canperform40%−60% thesamecapability,i.e.,usingthesamesizeoftheplaintext
2(cid:96)
betterthanontheprimefieldZ intermsofbandwidthcon- modulusandevaluatingthesameclassesoflinearfunctions.
p
sumption. Another reason to use Z instead of Z is that ThemainreasonliesintheimplementationofHEs.Mostof
2(cid:96) p
moduloreductioninZ isalmostfreeonstandardCPUs. thecurrentimplementationsoflattice-basedHEsapplythe
2(cid:96)
Howeverstate-of-the-artHE-basedprotocols[6,7,10,21, specialprimetechnique[20]toacceleratethecostlyhomo-
34]intheexisting2PC-NNsystemsforcethemtoexportthe morphic rotation at the cost of reducing the security level.
additivesecrettotheprimefieldZ butnottothemoreeffi- Tobringupthesecuritylevel,therotation-basedapproaches
p
cientchoiceZ .ThatisbecausetheseHE-basedprotocols havetobumpupthelatticedimension,andthustranslateto
2(cid:96)
heavilyutilizethehomomorphicSingle-Instruction-Multiple- slowerhomomorphicoperations.
Data(SIMD)technique[52]toamortizethecostofhomo-
morphicoperations.TheSIMDtechniqueinturndemandsa
1.1.3 LeanerProtocolsfortheNon-linearFunctions
primeplaintextmodulus pduetosomealgebraicconditions.
OnecanusetheChineseRemainderTheoremtoacceptsecret WiththeadventofsilentOTextension[9]builtuponvector
sharesfromZ usingaprimemodulus p≈2(cid:96)atthecostof obliviouslinearevaluation(VOLE),manycommunication-
2(cid:96)
increasingtheoverheadontheHE-sidebymany(e.g.,3–5) efficientOTextensions[14,56]areproposed,andtheland-
times. But this would ruin the gains of the non-linearpart. scapeofnon-linearfunctionevaluationdemandsfurtherin-
Infact,mostofthecurrentHE-hybridsystemsworkovera depthadaptation. [9,14,56]suggestthatgeneralsecuretwo-
primefieldandtoleratethelessefficientnon-linearprotocols. partycomputationcanbeupgradedbyusingVOLE-styleOT
Thisraisesthequestion:Couldwefindawaytoachievethe extension,but it remains to be seen how to design special-
bestofbothworlds?Thatistoenjoyamortizedhomomorphic purposeprimitivestofullybenefitfromVOLE-styleOT.Take
operationswhilekeepingtheefficientnon-linearprotocolson theintegercomparison(Millionaire)protocol,forexample,
theyardwithoutextraoverheads.Aswewillshow,thean- straightforwardlyupgradingtheOTextensionswithVOLE-
swerisyeswithournewdesignofHE-basedandSIMD-free styleOTextensionsdoesnotachievethebestperformance.
protocolsforthelinearfunctionsofDNNs. Wefurthermakeimprovementstothetruncationprotocol,
whichisrequiredaftereachmultiplicationsothatthefixed-
point values will not overflow. Truncation is expensive: It
1.1.2 FastandSIMD-freeLinearProtocols
contributes more than 50% of communication overhead in
Due to the spatial property of the convolution and matrix- CrypTFlow2.Ourimprovementsarebasedontwoimportant
vectormultiplication,itisinevitableforthepriorHE-based observations:First,thetruncationprotocolinCrypTFlow2is

designedtoeliminatetwoprobabilityerrorse ande where Table1:Comparisonwiththestate-of-the-artofsecure2PC
|     |     |     | 0   | 1   |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
Pr(|e |=1)=0.5andPr(0<|e |<2(cid:96))<ε(elaboratedin protocolsforthelinearfunctionsandnon-linearfunctionsin
| 0   |     | 1   |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
DNNs.Thelinearfunctionsincludetheconvolution(CONV),
§2.4).Withextensiveempiricalexperiments,weobservethat
theharsherrore isindeedproblematicbutthemild1-biter- batch normalization (BN),and fully connection (FC). The
1
rore barelyharmstheinferenceresults,evenforlarge-scale convolution and batch normalization take as input of a 3-
0
dimensiontensorT∈FC×H×W.Mandhdenotethenumber
DNNs.Thismotivatesustodesignmoreefficienttruncation
protocolsthateliminatee butkeepe untouched.Oursecond andthesizeofthefilters,respectively.Thefullyconnection
1 0
|                                                      |     |     |     |     | takesasinputofavectoru |     | ∈Fni | andoutputsavectoru | ∈   |
| ---------------------------------------------------- | --- | --- | --- | --- | ---------------------- | --- | ---- | ------------------ | --- |
| observationisthatsometimesthemostsignificantbit(MSB) |     |     |     |     |                        |     | i    |                    | o   |
Fno.Wewriten∗=min(n
isalreadyknownbeforethetruncation.Forinstanceweknow i ,n o )andn¯=max(n i ,n o ).Thenon-
thetheMSBis0ifthetruncationprotocolisexecutedright linearfunctionsincludethecomparisonoftwo(cid:96)-bitprivate
|              |                |           |                |       | integersandthetruncationofthelow |     |     | f-bitof(cid:96)-bitintegers. |     |
| ------------ | -------------- | --------- | -------------- | ----- | -------------------------------- | --- | --- | ---------------------------- | --- |
| after a ReLU | (i.e,max(0,x)) | protocol. | Similar to the | opti- |                                  |     |     |                              |     |
mizationfrom[45],weimplementatruncationprotocolfor λisthesecurityparameter(usuallyλ≥128).
thecaseofknownMSBusingVOLE-styleOT.Inaword,we
madealltheaboveoptimizations,resultinginfasterrunning LinearFunction Mult. Rotations
timeandbringingdownmorethan90%ofthecommunication
|     |     |     |     |     |     | [41,46] | O(MCHWh2) | O(MCHWh2) |     |
| --- | --- | --- | --- | --- | --- | ------- | --------- | --------- | --- |
CONV
| costofCrypTFlow2forthenon-linearlayers. |     |     |     |     |     | Cheetah | O(MCHW) | 0   |     |
| --------------------------------------- | --- | --- | --- | --- | --- | ------- | ------- | --- | --- |
Overall,wecomparethecomplexityofCheetah’sprotocols
|                                              |     |     |     |     |     | [46]    | O(CHW)  | 0           |          |
| -------------------------------------------- | --- | --- | --- | --- | --- | ------- | ------- | ----------- | -------- |
| withthestate-of-the-artcounterpartsinTable1. |     |     |     |     | BN  |         |         |             |          |
|                                              |     |     |     |     |     | Cheetah | O(CHW)  | 0           |          |
|                                              |     |     |     |     |     | [25]    | O(n n ) | O(n¯(n∗+log | (n o ))) |
| 1.2 OtherRelatedWork                         |     |     |     |     | FC  |         | o i     |             | 2 n ∗    |
|                                              |     |     |     |     |     | Cheetah | O(n n ) | 0           |          |
o i
Securecomputationofmachinelearninginferencealgorithms
|     |     |     |     |     | Non-linearFunction |     | Communication(bits) |     |     |
| --- | --- | --- | --- | --- | ------------------ | --- | ------------------- | --- | --- |
canperhapsdatebackto[8,23].CryptoNets[21]wasthefirst
|                                                        |     |     |     |     |         | [46]    |     | <λ(cid:96)+14(cid:96) |     |
| ------------------------------------------------------ | --- | --- | --- | --- | ------- | ------- | --- | --------------------- | --- |
| systemtoconsidersecuretwo-partyneuralnetworkinference. |     |     |     |     | Compare |         |     |                       |     |
|                                                        |     |     |     |     |         | Cheetah |     | <11(cid:96)           |     |
ThefollowingimprovementsafterCryptoNetscanberoughly
categorizedintothreeclasses.1)Optimizationsforthebasic [46] λ((cid:96)+f+2)+19(cid:96)+14f
Trunc
operationsofNNsuchasconvolutions[10,34],matrixmul- Cheetah 13(cid:96)
tiplications[33,40]andnon-linearactivationfunctions[19].
2)OptimizationsforaspecificclassofNN.Forinstance,NN
Weusethedotsymbol·suchasaˆ·bˆ
useslinearactivationfunctionsonly[7,17,27]andbinarized ofaˆ. torepresentthe
multiplicationofpolynomials.Fora2-powernumberN,and
NNs[2,47].3)Usingmixedprimitives(e.g.,GarbledCircuit,
q>0,wewriteA
TrustedExecutionEnvironment,HEandOT)toachievethe N,q todenotethesetofintegerpolynomials
|     |     |     |     |     | A =Z |     |     |     |     |
| --- | --- | --- | --- | --- | ---- | --- | --- | --- | --- |
[X]/(XN+1).Weuseboldupper-caseletterssuch
| bestperformanceforboththelinearandnon-linearfunctions |     |     |     |     | N,q | q   |     |     |     |
| ----------------------------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
asTtorepresentmulti-dimensiontensors,anduseT[c,i,j]
| in NNs | [6,34,39,43,53]. | Some other | works consider | the |     |     |     |     |     |
| ------ | ---------------- | ---------- | -------------- | --- | --- | --- | --- | --- | --- |
secure inference problem with more than two parties such todenotethe(c,i,j)entryofa3-dimensiontensorT.Weuse
boldlower-caseletterssuchasatorepresentvectors,anduse
as[15,16,37,42].TheseHE-freeapproachesareusuallymore
|     |     |     |     |     | a[j]todenotethe | j-thcomponentofa.Weusea(cid:62)btodenote |     |     |     |
| --- | --- | --- | --- | --- | --------------- | ---------------------------------------- | --- | --- | --- |
efficientthanthetwo-partycounterparts.Forinstance,[37]is
innerproductofvectors.
morethan15×fasterthanCrypTFlow2onResNet50.
|     |     |     |     |     | PolynomialArithmetic.Givenpolynomialsaˆ,bˆ |     |     |     | ∈A ,the |
| --- | --- | --- | --- | --- | ------------------------------------------ | --- | --- | --- | ------- |
N,q
|     |     |     |     |     | productdˆ=aˆ·bˆ | overA |     |     |     |
| --- | --- | --- | --- | --- | --------------- | ----- | --- | --- | --- |
isdefinedby
| 2 Preliminaries |     |     |     |     |        |                 | N,q                   |     |     |
| --------------- | --- | --- | --- | --- | ------ | --------------- | --------------------- | --- | --- |
|                 |     |     |     |     | dˆ[i]= | ∑ aˆ[j]bˆ[i−j]− | ∑ aˆ[j]bˆ[N+j−i]modq. |     | (1) |
2.1 Notations
|     |     |     |     |     | 0≤j≤i |     | i<j<N |     |     |
| --- | --- | --- | --- | --- | ----- | --- | ----- | --- | --- |
Wedenoteby[[n]]theset{0,···,n−1}forn∈N. Weuse (1)comesfromthefactthatXN ≡−1modXN+1.
(cid:100)·(cid:101),(cid:98)·(cid:99)and(cid:98)·(cid:101)todenotetheceiling,flooring,androunding
| function,respectively.WedenoteZ |     |     | =Z∩[−(cid:98)q/2(cid:99),(cid:98)q/2(cid:99)] |     |                                        |     |     |     |     |
| ------------------------------- | --- | --- | --------------------------------------------- | --- | -------------------------------------- | --- | --- | --- | --- |
|                                 |     |     | q                                             |     | 2.2 Lattice-basedHomomorphicEncryption |     |     |     |     |
forq≥2.Particularly,Z
2 denotestheset{0,1}.Forasigned
integerx,wewritex(cid:29) f todenotethearithmeticright-shift Ourprotocolsusetwolattice-basedHEs,i.e.,HEthatbased
ofxby f-bit.λisthesecurityparameter.WeuseFtodenote onlearningwitherrors(LWE)anditsringvariant(ring-LWE).
ageneralfield. ThelogicalAND,ORandXORis∧,∨and ThesetwoHEsshareasetofparametersHE.pp={N,σ,q,p}
⊕,respectively.Let1{P}denotetheindicatorfunctionthat suchthatq,p∈Zandq(cid:29)p>0wheretheplaintextmodulus
| is1whenP | istrueand0whenP | isfalse. |     |     | pcanbeanon-primevalue. |     |     |     |     |
| -------- | --------------- | -------- | --- | --- | ---------------------- | --- | --- | --- | --- |
Weuselower-caseletterswitha“hat”symbolsuchasaˆto The basic asymmetric RLWE encryption scheme uses
representapolynomial,andaˆ[j]todenotethe j-thcoefficient a secret polynomial as the secret key sk=sˆ∈A . The
N,q

associated public key is computed as pk=(uˆ ·sˆ+eˆ ,uˆ ) m oflength(cid:96)bitsandareceiverinputsachoicebitc∈{0,1}.
|     |     |     |     |     |     | 0   | 0 0 | 1   |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
whereuˆ ∈A ischosenuniformlyatrandom,andtheerror Attheendoftheprotocol,thereceiverlearnsm ,whereasthe
|     | 0   | N,q |     |     |     |     |     |     |     |     |     |     | c   |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
∈A
eˆ 0 N,q is chosen by sampling its coefficients from χ σ a senderlearnsnothing.OTisusuallyrealizedbybuildingafew
discreteGaussiandistributionofstandarddeviationofσ.The baseOTinstanceswithpublickeycryptographyandextend-
RLWEencryptionofamessagemˆ ∈A isgivenasatupleof ingtoalargeamountofinstanceswithefficientsymmetric
N,p
q
polynomialsRLWEN,q,p(mˆ)=((cid:98) mˆ(cid:101)+eˆ,0)−uˆ·pk∈A2 , cryptographicoperations(IKNPOTextension[31]).When
|     |     |     | pk  |     |     |     | N,p |                                                   |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ------------------------------------------------- | --- | --- | --- | --- | --- | --- |
|     |     |     |     | p   |     |     |     | sendermessagesarerandomorcorrelatedinaway,general |     |     |     |     |     |     |
ofeˆ∈A
| where | the coefficients |     |     | N,q | is sampledfrom |     | χ σ and |     |     |     |     |     |     |     |
| ----- | ---------------- | --- | --- | --- | -------------- | --- | ------- | --- | --- | --- | --- | --- | --- | --- |
OTcanbereplacedwithrandomOT(ROT)orcorrelatedOT
| the coefficients |     | of  | uˆ ∈ A | is chosen |     | from {0,±1} | uni- |                                                   |     |     |                 |     |     |     |
| ---------------- | --- | --- | ------ | --------- | --- | ----------- | ---- | ------------------------------------------------- | --- | --- | --------------- | --- | --- | --- |
|                  |     |     |        | N,q       |     |             |      | (COT)whicharemoreefficientincommunication[3].More |     |     |                 |     |     |     |
|                  |     |     |        |           |     | (bˆ,aˆ)     |      |                                                   |     |     | (cid:0)n(cid:1) |     |     |     |
formly at random. A RLWE ciphertext is decrypted general 1-out-of-N OT -OT can be implemented in an
|     |     |     | p   |     |     |     |     |     |     |     | 1   | (cid:96) |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | -------- | --- | --- |
asRLWE− 1(bˆ,aˆ)=(cid:98) (bˆ+aˆ·sˆ)(cid:101)≡mˆ (cid:0)2 (cid:1)
|     |     |     |     |     | mod | p.  |     | IKNP-styleOTextension,orwithlog |     |     |     | ncallsto |     | -OT [44]. |
| --- | --- | --- | --- | --- | --- | --- | --- | ------------------------------- | --- | --- | --- | -------- | --- | --------- |
|     | sk  |     | q   |     |     |     |     |                                 |     |     |     | 2        | 1   | λ         |
Inourprotocols,weusethenotationLWEN,q,p(m)tode- Recently,[9]proposesilentOTextension,wherealarge
s
amountofrandomOTcorrelationscanbegeneratedwitha
| note | the LWE | encryption |     | of a | message | m ∈ | Z under a |     |     |     |     |     |     |     |
| ---- | ------- | ---------- | --- | ---- | ------- | --- | --------- | --- | --- | --- | --- | --- | --- | --- |
p
secret vector s ∈ ZN. The LWE ciphertext of m is given low-communication input-independent setup and a second
q
phaseofpurelocalcomputation.Thetechniqueislaterim-
| as a | tuple (b,a)∈ZN+1 |     |     | and it is | decrypted | by  | computing |     |     |     |     |     |     |     |
| ---- | ---------------- | --- | --- | --------- | --------- | --- | --------- | --- | --- | --- | --- | --- | --- | --- |
p
|                     |     | p   |                              |     |                   |     |     | proved                                                 | with | more efficient | computation |     | in Ferret | [56] and |
| ------------------- | --- | --- | ---------------------------- | --- | ----------------- | --- | --- | ------------------------------------------------------ | ---- | -------------- | ----------- | --- | --------- | -------- |
| LWE−1(b,a)=(cid:98) |     |     | (b+a(cid:62)s)(cid:101)≡mmod |     | p.Tolightentheno- |     |     |                                                        |      |                |             |     |           |          |
|                     | s   |     |                              |     |                   |     |     | Silver[14].Withlittlecommunicationcost,theseVOLE-style |      |                |             |     |           |          |
q
OTspavethewayforthepossibilityofnext-generationsecure
tation,weunifythesecretofLWEandRLWEciphertextsby
identifying the LWE secret s[j]=sˆ[j] forall j∈[[N]]. We computation.WeuseVOLE-styleOTasabuildingblockfor
writetheLWEencryptionofmasLWEn,q,p(mˆ)fromnowon. moreefficientdesignsofnon-linearlayersinDNNinference.
sk
Theproposedprotocolleveragesthefollowingfunctions
supportedbytheRLWEencryption.
2.4 ArithmeticSecretSharing
• Homomorphicaddition((cid:1))andsubtraction((cid:12)).Given
| RLWE | ciphertexts |     | CT  | and CT | ,which | respectively | en- |     |     |     |     |     |     |     |
| ---- | ----------- | --- | --- | ------ | ------ | ------------ | --- | --- | --- | --- | --- | --- | --- | --- |
0 1 Forthearithmeticsecretsharing,an(cid:96)-bitvaluexisshared
| cryptsapolynomial |     |     | pˆ  | and pˆ ,theoperationCT |     |     | (cid:1)CT |     |     |     |     |     |     |     |
| ----------------- | --- | --- | --- | ---------------------- | --- | --- | --------- | --- | --- | --- | --- | --- | --- | --- |
0 1 0 1 additivelyintheringZ asthesumoftwovalues,say(cid:104)x(cid:105)A
|     |     | (cid:12)CT |     |     |     |     | T(cid:48)tha |     |     |     |     |     |     |     |
| --- | --- | ---------- | --- | --- | --- | --- | ------------ | --- | --- | --- | --- | --- | --- | --- |
(resp.CT 0 1 )resu ltsatan RLWEciphertextC t 2(cid:96) 2(cid:96)
and(cid:104)x(cid:105)B
decryptsto pˆ +pˆ ∈A (resp. pˆ −pˆ ). 2(cid:96) .Toreconstructthevaluex,wecomputethemodulo
|                                   |     | 0   | 1              | N,p | 0          | 1                 |          |                                      |     |                                  |                                    |                                 |     |     |
| --------------------------------- | --- | --- | -------------- | --- | ---------- | ----------------- | -------- | ------------------------------------ | --- | -------------------------------- | ---------------------------------- | ------------------------------- | --- | --- |
|                                   |     |     |                |     |            |                   |          | addition,i.e.,x≡(cid:104)x(cid:105)A |     |                                  | +(cid:104)x(cid:105)B              | mod2(cid:96).Inthetwo-partyset- |     |     |
|                                   |     |     |                |     | ((cid:2)). |                   |          |                                      |     |                                  | 2(cid:96) 2 (cid:96)               |                                 |     |     |
| • Homomorphic                     |     |     | multiplication |     | Given      | an                | RLWE ci- | ting,valuex∈Z                        |     |                                  |                                    |                                 |     |     |
|                                   |     |     |                |     |            |                   |          |                                      |     | (cid:96) iss                     | ecretly s haredbetweenAliceandBob, |                                 |     |     |
| phertextCTthatencryptsapolynomial |     |     |                |     |            | pˆ,andgivenaplain |          |                                      |     | 2                                |                                    |                                 |     |     |
|                                   |     |     |                |     |            |                   |          | bylettingAliceh                      |     | o ldtheshare(cid:104)x(cid:105)A |                                    | andlettingBobholdthe            |     |     |
elementcˆ∈A ,theoperationcˆ(cid:2)CTresultsatanRLWE 2(cid:96)
N , p
|                      |     |     |              |     |         |     |     | share(cid:104)x(cid:105)B | .Also,wewillomitthesubscriptifthemodulo2(cid:96) |     |     |     |     |     |
| -------------------- | --- | --- | ------------ | --- | ------- | --- | --- | ------------------------- | ------------------------------------------------ | --- | --- | --- | --- | --- |
| ciphertextCT(cid:48) |     | t h | atdecryptsto |     | pˆ·cˆ∈A | .   |     |                           | 2(cid:96)                                        |     |     |     |     |     |
|                      |     |     |              |     |         | N,p |     | isclearfromthecontext.    |                                                  |     |     |     |     |     |
• Extract. Given (bˆ,aˆ)=RLWEN,q,p(mˆ) of mˆ we can ex- Fixed-point Values and Truncation. Mostpriorworks on
pk
2PCusefixed-pointarithmetic,wherearealvaluex˜∈Risen-
| tract | an LWE | ciphertext |     | of the | k-th coefficient |     | of mˆ, i.e., |     |     |     |     |     |     |     |
| ----- | ------ | ---------- | --- | ------ | ---------------- | --- | ------------ | --- | --- | --- | --- | --- | --- | --- |
(b,a)=Extract((bˆ,aˆ),k).Thetuple(b,a)isavalidLWE codedasafixed-pointvaluex=(cid:98)x˜2f(cid:99)∈Zunderaspecified
ciphertextofmˆ[k]underthesecretkeysk.Thishastheeffect
|     |     |     |     |     |     |     |     | precision | f   | >0.Themultiplicationoftwofixed-pointvalues |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --------- | --- | ------------------------------------------ | --- | --- | --- | --- |
ofavoiding extra information leakage when onlycertain of f-bitprecisionresultsatafixed-pointvalueof2f-bitpre-
coefficientsareexpectedtobereceivedbyaparty.Wedefer cision.Inordertodosubsequentarithmetics,atruncationis
f-bitprecision.Suppose(cid:104)x(cid:105)A
thedetailsofExtracttoChenetal.’spaper[13,§3.3]. requiredtoscaledownto and
2(cid:96)
(cid:104)x(cid:105)B arethesharesofadouble-precisionvalue,i.e.,(cid:98)x˜22f(cid:99).
2(cid:96)
| By setting |     | a prime | p≡1mod2N,it |     | is  | possible | to use the |                                                           |     |     |     |     |                         |     |
| ---------- | --- | ------- | ----------- | --- | --- | -------- | ---------- | --------------------------------------------------------- | --- | --- | --- | --- | ----------------------- | --- |
|            |     |         |             |     |     |          |            | Afaithfultruncationprotocolshouldtake(cid:104)x(cid:105)A |     |     |     |     | and(cid:104)x(cid:105)B | as  |
SIMDtechnique[52]toamortizethecostofhomomorphic 2(cid:96) 2(cid:96)
inputandcomputethesharesof(cid:98)x˜22f(cid:99)(cid:29)
f.
multiplications.Forinstance,[25]computestheinnerproduct
oftwoencryptedvectorofN elementsusingonehomomor- TruncationErrors.Thelocaltruncationprotocolof[43]in-
phicmultiplicationandO(log (N))homomorphicrotations. troducesprobabilityerrors.Forexample,toperformthelocal
2
|     |     |     |     |     |     |     |     | truncationon(cid:104)x(cid:105)A |     | and(cid:104)x(cid:105)B | ,twoshareholdersset(cid:104)x(cid:48)(cid:105)A |     |     | =   |
| --- | --- | --- | --- | --- | --- | --- | --- | -------------------------------- | --- | ----------------------- | ----------------------------------------------- | --- | --- | --- |
CheetahdoesnotuseSIMDan drotations,sowedeferthese 2(cid:96) 2(cid:96) 2(cid:96)
detailstoAppendixB. (cid:98)(cid:104)x(cid:105)A /2f(cid:99)and(cid:104)x(cid:48)(cid:105)B =2(cid:96)−(cid:98)2(cid:96)−(cid:104)x(cid:105)B /2f(cid:99)mod2(cid:96),respec-
|     |                   |     |     |     |     |     |     |                                  | 2(cid:96) | 2(cid:96)    |                                | 2(cid:96) |                        |           |
| --- | ----------------- | --- | --- | --- | --- | --- | --- | -------------------------------- | --------- | ------------ | ------------------------------ | --------- | ---------------------- | --------- |
|     |                   |     |     |     |     |     |     | tively.Thenthevaluex(cid:48)     |           |              | equalsto(cid:98)x˜2f(cid:99)+e |           | +e                     | withtwo   |
|     |                   |     |     |     |     |     |     |                                  |           |              |                                |           | 0                      | 1         |
|     |                   |     |     |     |     |     |     | probability                      |           | errors where | the small                      | error     | |e |≤1                 | occurs at |
| 2.3 | ObliviousTransfer |     |     |     |     |     |     |                                  |           |              |                                |           | 0                      |           |
|     |                   |     |     |     |     |     |     | thechanceof1/2andtheharsherror|e |           |              |                                |           | |<2(cid:96) occurswith |           |
1
achanceofx/2(cid:96).
Ourprotocolsrelyheavilyonoblivioustransfer(OT)fornon- Todecreasestheprobabilityoftheharsh
linearcomputation(e.g.,comparison).Inageneral1-out-of-2 errore ,alargerbitlength(cid:96)isneeded.Thisrendersalarger
1
OT,denotedby (cid:0)2(cid:1) -OT ,asenderinputstwomessagesm and overheadonbothoflinearprotocolsandnon-linearprotocols.
|     |     |     | (cid:96) |     |     |     | 0   |     |     |     |     |     |     |     |
| --- | --- | --- | -------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
1

2.5 SecureNeuralNetworkInference Parameters:Shapemetani,no>0.
|     |     |     |     |     |     |     |     | Computation: | On input | (cid:104)v(cid:105)A ∈Fni,W∈Fno×ni | and b∈Fno |
| --- | --- | --- | --- | --- | --- | --- | --- | ------------ | -------- | ---------------------------------- | --------- |
In this section we describe an abstraction of DNN and set fromAliceandinput(cid:104)v(cid:105)B∈Fni fromBob,computeu=Wv+b.
upthesecureneuralinferenceproblemthatwewilltacklein SampleanuniformvectorrfromFno.
Return:rtoAliceandv−r∈F∗toBob.
therestofthemanuscript.DNNtakesaninputx(e.g.,RGB
image)andprocessesitthroughasequenceoflinearandnon-
(a)IdealFunctionalityFFC
linearlayersinordertoclassifyitintooneofthepotential
classes, e.g., z = f d (f d−1 (···(f 1 (x,W 1 ),···),W d−1 ),W d ) Parameters:ShapemetaM,C,H,W,handstrides>0.
where f isthefunctionevaluatedinthed-thlayerandW Computation:Oninput(cid:104)T(cid:105)A∈FC×H×W,K∈FM×C×h×hfrom
| d   |     |     |     |     |     |     | d   |     |                      |        |           |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | -------------------- | ------ | --------- |
|     |     |     |     |     |     |     |     |     | (cid:104)T(cid:105)B | FC×H×W | T(cid:48) |
is the weight parameter(s) used in that layer. Suppose we Alice and input ∈ from Bob, compute =
Conv2D(T,K;s).SampleanuniformtensorRfromFwiththe
alreadyhave2PCprotocolsthattakesecret-sharedinputsand
| output secret-shared |     | results | for | the functions |     | f ,f ,···,f | ,   | sameshapeofT(cid:48). |     |     |     |
| -------------------- | --- | ------- | --- | ------------- | --- | ----------- | --- | --------------------- | --- | --- | --- |
|                      |     |         |     |               |     | 1 2         | d   |                       |     |     |     |
Return:RtoAliceandT(cid:48)−R∈F∗toBob.
| to achieve | the secure | inference,we |     | can | simply | invoke | the |     |     |     |     |
| ---------- | ---------- | ------------ | --- | --- | ------ | ------ | --- | --- | --- | --- | --- |
corresponding2PCprotocolssequentially. (b)IdealFunctionalityFCONV
Wenowdescribethefunctionswearetargetting,andthen
presenthowtoevaluatethosefunctionsprivately. Parameters:ShapemetaC,H,W.
Computation:Oninput(cid:104)T(cid:105)A∈FC×H×W,µ,θ∈FCfromAlice
|     |     |     |     |     |     |     |     | andinput(cid:104)T(cid:105)B∈FC×H×W |     | fromBob,computeT(cid:48)=BN(T;µ,θ). |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ----------------------------------- | --- | ----------------------------------- | --- |
2.5.1 LinearLayers SampleanuniformtensorRfromFwiththesameshapeofT(cid:48).
Return:RtoAliceandT(cid:48)−R∈F∗toBob.
FullyConnectedLayer(FC).Theinputtoafullyconnected
layerisavectorv∈Fni oflengthn anditsoutputisavector (c)IdealFunctionalityFBN
i
u∈Fno
|                                | oflengthn           | .Afullyconnectedlayerisparameterized |     |                        |                   |         |     |                                            |     |     |     |
| ------------------------------ | ------------------- | ------------------------------------ | --- | ---------------------- | ----------------- | ------- | --- | ------------------------------------------ | --- | --- | --- |
|                                |                     | o                                    |     |                        |                   |         |     | Figure1:IdealFunctionalitiesofLinearLayers |     |     |     |
| bythetuple(W,b)whereW∈Fno×ni   |                     |                                      |     |                        | istheweightmatrix |         |     |                                            |     |     |     |
| andbisann                      | o -sizedbiasvector. |                                      |     | Theoutputisspecifiedby |                   |         |     |                                            |     |     |     |
| thelineartransformationu=Wv+b. |                     |                                      |     |                        |                   |         |     | 2.5.2 Non-linearLayers                     |     |     |     |
| Convolution                    | Layer               | (CONV).                              | A   | two                    | dimensional       | strided |     |                                            |     |     |     |
Inthecontextofdeeplearning,thenon-linearlayersconsist
| convolution | Conv2D(T,K;s) |     | over | a field | F operates |     | on a |     |     |     |     |
| ----------- | ------------- | --- | ---- | ------- | ---------- | --- | ---- | --- | --- | --- | --- |
ofanactivationfunctionthatactsoneachelementoftheinput
| 3-dimensiontensorT∈FC×H×W |     |     |     | withastrides>0andaset |     |     |     |     |     |     |     |
| ------------------------- | --- | --- | --- | --------------------- | --- | --- | --- | --- | --- | --- | --- |
independentlyorapoolingfunctionthatreducestheoutput
ofkernels(alsocalledfilters)representedbya4-dimension
size.Typicalnon-linearfunctionscanbeoneofseveraltypes:
tensorK∈FM×C×h×htogeneratea3-dimensionoutputten-
T(cid:48) ∈FM×H(cid:48)×W(cid:48) H(cid:48) =(cid:98)(H−h+s)/s(cid:99) andW(cid:48) = the mostcommon ones in DNNs are ReLU functions (i.e.,
| sor |     | where |     |     |     |     |     |     |     |     |     |
| --- | --- | ----- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
ReLU(x)=max(0,x))andmax-poolingfunctions.Inthecon-
(cid:98)(W−h+s)/s(cid:99).IfTisanRGBimagethenC=3andH,W
textof2PC,truncationisalsoconsideredasanon-linearlayer
denotetheheightandwidthoftheimage,respectively.Also,
becausetruncationisbeyondtheabilityofarithmeticcircuit.
Mdenotesthenumberofkernelsusedintheconvolutionand
FollowingtheblueprintofCrypTFlow2,thesenon-linearlay-
histhesizeofthekernels.
erscanbeevaluatedsecurelyviaOT-basedprotocols.
| From | a mathematical |     | viewpoint, | the | two | dimensional |     |     |     |     |     |
| ---- | -------------- | --- | ---------- | --- | --- | ----------- | --- | --- | --- | --- | --- |
stridedconvolutioncanbeseenascalculatingweightedsums
|                                           |     |                                                                     |     |     |     |     |     | 2.5.3 Two-PartyInferenceSystem&ThreatModel |     |     |     |
| ----------------------------------------- | --- | ------------------------------------------------------------------- | --- | --- | --- | --- | --- | ------------------------------------------ | --- | --- | --- |
| T(cid:48)[c(cid:48),i(cid:48),j(cid:48)]= |     | ∑ T[c,i(cid:48)s+l,j(cid:48)s+l(cid:48)]K[c(cid:48),c,l,l(cid:48)]. |     |     |     |     |     |                                            |     |     |     |
(2)
|     |     |     |     |     |     |     |     | Suppose | the secure inference | is executed | jointly by Alice |
| --- | --- | --- | --- | --- | --- | --- | --- | ------- | -------------------- | ----------- | ---------------- |
c ∈ [[ C ]]
l(cid:48) (Server)andBob(Client).LetI andI betheprivateinputof
|     |     | l, ∈ [ [h ]] |     |     |     |     |     |     |     | A B |     |
| --- | --- | ------------ | --- | --- | --- | --- | --- | --- | --- | --- | --- |
AliceandBobtoatwo-partyprotocolsayΠ,respectively.We
foreachposition(c(cid:48),i(cid:48),j(cid:48))oftheoutputtensorT(cid:48). writeO A ,O B ←Π(I A ,I B )todenoteanexecutionofΠwhere
Batch Normalization Layer (BN). In DNNs, a BN layer O andO aretheoutputtoAliceandBob,respectively.
|     |     |     |     |     |     |     |     | A   | B   |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
BN(T;α,β) takes as input of 3-dimension tensor T ∈ WetargetthesamethreatmodelofDELPHIandCrypT-
FC×H×W and output a 3-dimension tensor T(cid:48) of the same Flow2. Cheetah is designed for the two-party semi-honest
settinginwhichbothofpartiesfollowthespecificationofthe
| shape. An | BN layer | is specified |     | by the | tuple | (µ,θ) where |     |     |     |     |     |
| --------- | -------- | ------------ | --- | ------ | ----- | ----------- | --- | --- | --- | --- | --- |
µ∈FC isthescalingvectorandθ∈FC istheshiftvector.For protocolandonlyoneofthethemiscorruptedbyanadversary.
allc∈[[C]],i∈[[H]]and j∈[[W]],T(cid:48)iscomputedvia Inthecontextofcryptographicinference,AliceholdsaDNN
whileBobholdsaninputtothenetwork,typicallyanimage.
T(cid:48)[c,i,j]=µ[c]T[c,i,j]+θ[c]. (3) Byassumingsemi-honestAliceandBob,oursystemenables
Bobtolearnonlytwopiecesofinformation:thearchitecture
ByviewingeachchannelofTasaHW-sizedvector,wecan oftheneuralnetwork(i.e.,thenumberoflayers,thetypeof
naturallyrewritetheBNevaluationtoaformthatinvolves layers,andthesizeofeachlayer),andtheinferenceresult.Al-
scalar-vectormultiplicationsandvectoradditionsonly. iceiseitherallowedtolearntheresultornothing,depending

ontheapplicationscenario.AllotherinformationaboutBob’s Inputs&Outputs:
privateinputsandtheparametersofAlice’sneuralnetwork
(cid:104)u(cid:105)A,(cid:104)u(cid:105)B←HomFC({(cid:104)v(cid:105)A,W,b},{(cid:104)v(cid:105)B,sk})
modelshouldbekeptsecret.Weprovideformaldefinitions
ofthreatmodelinAppendixA. W∈Zn po×ni,b∈Zn po,(cid:104)v(cid:105)A,(cid:104)v(cid:105)B∈Zn pi,andu=Wv+b∈Zn
po.
Likeallthepriorsemi-honestinferencesystems,Cheetah
|     |     |     |     |     | PublicParameters:pp=(HE.pp,pk,n |     |     |     |     | ,n  | o ,n ,n ow | ).  |
| --- | --- | --- | --- | --- | ------------------------------- | --- | --- | --- | --- | --- | ---------- | --- |
|     |     |     |     |     |                                 |     |     |     |     | i   | iw         |     |
wasnotdesignedtodefendagainstattacksbasedpurelyon
|     |     |     |     |     | •   | Shapemetan | i ,n osuchthatn |     | i ,n o | >0.Thepartitionwindow |     |     |
| --- | --- | --- | --- | --- | --- | ---------- | --------------- | --- | ------ | --------------------- | --- | --- |
theinferenceresults(suchastheAPIattacks[51,54]).Indeed,
|     |     |     |     |     |     | size0<n | ≤n   | ,0<n | ≤n suchthatn |     | n ≤N. |     |
| --- | --- | --- | --- | --- | --- | ------- | ---- | ---- | ------------ | --- | ----- | --- |
|     |     |     |     |     |     |         | iw i | ow   | i            |     | iw ow |     |
wecanintegrateorthogonaltechniquessuchasdifferential
|     |     |     |     |     | •   | Setn (cid:48)=(cid:100)n | /n (cid:101)andn |     | (cid:48)=(cid:100)n /n | (cid:101). |     |     |
| --- | --- | --- | --- | --- | --- | ------------------------ | ---------------- | --- | ---------------------- | ---------- | --- | --- |
privacy[1,32]toprovideanevenstrongerprivacyguarantee. i i iw o o ow
(cid:104)v(cid:105)B
|                                      |     |     |     |     |     | 1: Bob                                           | first partitions   | its | input shares             |     | into          | subvectors    |
| ------------------------------------ | --- | --- | --- | --- | --- | ------------------------------------------------ | ------------------ | --- | ------------------------ | --- | ------------- | ------------- |
|                                      |     |     |     |     |     | (cid:104)v (cid:105)B∈Zn                         | iwforα∈[[n(cid:48) |     | ]].Zero-paddingthemwhenn |     |               | (cid:45)n .   |
| 3 Proposed2PCProtocolsofLinearLayers |     |     |     |     |     | α                                                | p                  |     | i                        |     |               | i iw          |
|                                      |     |     |     |     |     |                                                  |                    |     |                          |     | (cid:105)B=πi | (cid:105)B)   |
|                                      |     |     |     |     |     | 2: Bobencodesthevectorstopolynomials(cid:104)vˆα |                    |     |                          |     |               | ((cid:104)v α |
|                                      |     |     |     |     |     |                                                  | [[n(cid:48)        |     |                          |     |               | fc            |
ThecorecomputationinFC,CONVandBNcanberewritten for α ∈ ]]. Then Bob sends the RLWE ciphertexts
i
|     |     |     |     |     |     | {CT(cid:48) | =RLWEN | ,q,p((cid:104)vˆα | (cid:105)B)}toAlice. |     |     |     |
| --- | --- | --- | --- | --- | --- | ----------- | ------ | ----------------- | -------------------- | --- | --- | --- |
as a batch of inner products. In deep neural networks,the α pk
fan-intotheinnerproductcircuitcanbelarge,leadingavast 3: Similarly,Alicefirstpartitionsitsshares(cid:104)v(cid:105)Ainto(cid:104)v (cid:105)A∈
α
numberofhomomorphicmultiplications.Toamortizethecost Zn iw following the same manner in Step 1. Also, Alice
p
of multiplications,most of the prior HE-based approaches partitions the weightmatrixW into blockmatris W β,α ∈
choosetousetheSIMDtechnique.Aswehavementioned, Zn ow ×niw. Zero-padding is used to the right-most (resp.
p
|     |     |     |     |     |     | bottom-most)blockswhen |     |     | n (cid:45)n | (resp. | n (cid:45)n | ). Then |
| --- | --- | --- | --- | --- | --- | ---------------------- | --- | --- | ----------- | ------ | ----------- | ------- |
thesum-stepintheinnerproductcircuitdemandsexpensive i iw o ow
homomorphicrotations.AlsotheSIMDtechniquerequires Aliceencodesthesubvectorsandblockmatricestopolyno-
|     |     |     |     |     |     |     | (cid:105)A=πi | (cid:105)Aandwˆ |     | =πw |     |     |
| --- | --- | --- | --- | --- | --- | --- | ------------- | --------------- | --- | --- | --- | --- |
plaintextfromaprimefieldZ suchthat p≡1mod2N. mials(cid:104)vˆα (cid:104)v α (W )forα∈[[n(cid:48) ]]
|     |     | p   |     |     |     |     |     | fc  | β,α | fc  | β,α | i   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
andβ∈[[n(cid:48)]].
| Ontheotherhand,ourlinearprotocolsarefreeofSIMD |     |     |     |     |     |     | o   |     |     |     |     |     |
| ---------------------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
4: Onreceivingtheciphertexts{CT(cid:48)}fromBob,Aliceoper-
| andhomomorphicrotation.Weobservethatthepolynomial |     |     |     |     |     |        |            |                         |                  | α                  |                  |                 |
| ------------------------------------------------- | --- | --- | --- | --- | --- | ------ | ---------- | ----------------------- | ---------------- | ------------------ | ---------------- | --------------- |
|                                                   |     |     |     |     |     |        | (cid:1)    |                         | (cid:48) (cid:1) | (cid:105)A (cid:2) |                  | (cid:48)        |
|                                                   |     |     |     |     |     | a te s | C T β = α∈ | [ [ n(cid:48) ] ] ( ( C | T α (cid:104)vˆ  | α )                | w ˆ β ,α ) f o r | β ∈ [ [n o ]] . |
m u l t ip l i ca ti on (1 ) i ts e lf c an b e v i e w e d a s a b a t c h o f in n e r i
|     |     |     |     |     |     | 5: [E x t | ra c ta nd R | e - m a s k | .] A l ice s | am p l es | r ∈ Z n o u | n if or m l y a t |
| --- | --- | --- | --- | --- | --- | --------- | ------------ | ----------- | ------------ | --------- | ----------- | ----------------- |
pr o d u c t s if w ea rr a n g e th e co e ffi c i e nt s p ro p er l y . I n th is s e c - p
randomtore-maskthecomputingciphertexts.Specifically,
| tion,wepresentanduseapairofnaturalmappings(πi |     |     |     | ,πw) |     |         |       |          |                |     |        |            |
| --------------------------------------------- | --- | --- | --- | ---- | --- | ------- | ----- | -------- | -------------- | --- | ------ | ---------- |
|                                               |     |     |     | F F  |     |         | i∈[[n | ]],Alice |                |     |        |            |
|                                               |     |     |     |      |     | foreach |       | o        | first extracts |     | an LWE | ciphertext |
t o p r o p e r l y p l a c e t h e v a l u e s i n th e in p u t a n d w e ig h t t o p o l y - (cid:48)
|     |     |     |     |     |     | c t i = | E x t r a c t ( C | T i m o d n | (cid:48) , ( i m o d | n o ) n i | + n i − 1) | a nd t he nr e - |
| --- | --- | --- | --- | --- | --- | ------- | ----------------- | ----------- | -------------------- | --------- | ---------- | ---------------- |
n o m i a l c o e f fi c ie n t s f o r e a c h o f t h e fu n c ti o n al i t y F i n F i gu r e 1 . o
|     |     |     |     |     |     | m a s | k s i t v i a c t (cid:48) | = ct i (cid:12) | r [ i ] . A l | ic e t h e n | s e n ds th | e L W E c i- |
| --- | --- | --- | --- | --- | --- | ----- | -------------------------- | --------------- | ------------- | ------------ | ----------- | ------------ |
|     | i w |     |     |     |     |       | i                          |                 |               |              |             |              |
W i th th e h e l p o f ( π , π ) , w e t h e n s h o w h o w t o e v a l u a t e t h e s e p h e r te x t s { c t (cid:48) } b a c k t o B o b .
|     | F F |     |     |     |     |     | i   |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
functionalitiesprivately.Also,πi andπw arewell-definedfor pastheshare(cid:104)u(cid:105)A.
|     |     | F   | F   |     |     | 6: Aliceoutputsr+bmod |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --------------------- | --- | --- | --- | --- | --- | --- |
receivingtheLWEciphertexts{ct(cid:48)
any p>1suchas p=2(cid:96),allowingourprotocolstoaccept 7: On }from Alice,Bob
i
|     |     |     | Z   |     |     | computes(cid:104)u(cid:105)B[i]=LWE− |     |     | 1(ct(cid:48) )foralli∈[[n |     | ]]. |     |
| --- | --- | --- | --- | --- | --- | ------------------------------------ | --- | --- | ------------------------- | --- | --- | --- |
secretly shared input from the ring 2(cid:96) forfree. All above sk i o
makesourprotocolsfundamentallydifferentfromtheprevi-
ousSIMD-basedapproaches. Figure2:ProposedSecureFullyConnectionProtocol
| 3.1 FullyConnection |     |     |     |     | A   |     |     |     |     |     |     |     |
| ------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
N,p directlygivesthematrix–vectormultiplicationWv≡
|     |     |     |     |     | umod | pinsomeofitscoefficients. |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | ---- | ------------------------- | --- | --- | --- | --- | --- | --- |
Wepresentour2PCprotocolforFClayersinFigure2.The
corecomputationinanFClayeristhematrix-vectormultipli-
|                                                 |     |     |     |     | Proposition1 |     | Given   | two            | polynomials |     | vˆ = πi | (v),wˆ = |
| ----------------------------------------------- | --- | --- | --- | --- | ------------ | --- | ------- | -------------- | ----------- | --- | ------- | -------- |
| cationu=Wvwhichcanbedecomposedintoinnerproducts |     |     |     |     |              |     |         |                |             |     |         | fc       |
|                                                 |     |     |     |     | πw(W)        | ∈   | A , the | multiplication |             | Wv  | ≡ umod  | p can be |
|                                                 |     |     |     |     | fc           |     | N, p    |                |             |     |         |          |
ofvectors.Ourmappingfunctionsπw andπi arespecialized overtheringA
|     |     |     | fc fc |     | ev aluatedvia |     | t heproductuˆ=vˆ·wˆ |     |     |     |     | N,p .That |
| --- | --- | --- | ----- | --- | ------------- | --- | ------------------- | --- | --- | --- | --- | --------- |
forcomputingtheinnerproductusingpolynomialarithmetic.
|     |     |     |     |     | isu[i]iscomputedinuˆ[i·n |     |     |     | +n −1]foralli∈[[n |     |     | ]]. |
| --- | --- | --- | --- | --- | ------------------------ | --- | --- | --- | ----------------- | --- | --- | --- |
|     |     |     |     |     |                          |     |     |     | i i               |     |     | o   |
Intuitively,whenmultiplyingtwopolynomialsofdegree-N,
the(N−1)-thcoefficientoftheresultingpolynomialisthe Proof1 Foreachi∈[[n ]],wewriten˜ =i·n +n −1forsim-
|              |            |             |                     |     |                           |     |     | o                       |     | i   | i i |        |
| ------------ | ---------- | ----------- | ------------------- | --- | ------------------------- | --- | --- | ----------------------- | --- | --- | --- | ------ |
| innerproduct | of the two | coefficient | vectors in opposite | or- |                           |     |     |                         |     |     |     |        |
|              |            |             |                     |     | plicity.Bythedefinitionof |     |     | (1)andbecausevˆ[j]=0for |     |     |     | j≥n, i |
d e r s . W e c a ne a s i ly e xt e n d t h i s i de a t o a b a t c h o f in ne r pr o d - w e h av e uˆ [ n˜ ] = ∑ vˆ[j]wˆ[n − j]=∑ v[j]W[i, j]
|     |     |     |     |     |     |     | i 0 | ≤j<ni | i   |     | 0≤j<ni |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ----- | --- | --- | ------ | --- |
uc t s . W e n o w g i v e th e d e fi n i ti o n s o f π w : Z n o × n i (cid:55)→ A a n d w h ic h is e x a c tl yu [i ]. (cid:4)
|     |     |     | fc p | N ,p |     |     |     |     |     |     |     |     |
| --- | --- | --- | ---- | ---- | --- | --- | --- | --- | --- | --- | --- | --- |
πi :Zni(cid:55)→A
| p   | N,p .Herewefirstrequiren |     | o n i ≤Nforsimplicity. |     |                                                          |     |     |     |     |     |     |     |
| --- | ------------------------ | --- | ---------------------- | --- | -------------------------------------------------------- | --- | --- | --- | --- | --- | --- | --- |
| fc  |                          |     |                        |     | InProposition1,othercoefficientsbesidesuˆ[n˜]inuˆcontain |     |     |     |     |     |     |     |
i
vˆ=πi
(v)wherevˆ[j]=v[j] (4) extrainformationbeyondWv.Topreventsuchleakage,Alice
fc
=πw(W)wherewˆ[i·n usestheExtract(·)functiontoextracttheneededcoefficients
| wˆ  |     | +n  | −1−j]=W[i,j], |     |     |     |     |     |     |     |     |     |
| --- | --- | --- | ------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|     | fc  | i   | i             |     |     |     |     |     |     |     |     |     |
fromuˆ.WepresentatoyexampleinFigure3.
wherei∈[[n ]],j∈[[n]]andallothercoefficientsofvˆand When nn >N,we can firstpartition the weightmatrix
|     | o i |     |     |     |     |     | i o |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
wˆ aresetto0.Themultiplicationofpolynomialsuˆ=wˆ·vˆ∈ intosub-matricesof0<n¯ ×n¯ elementssuchthatn¯n¯ ≤N
|     |     |     |     |     |     |     |     | i   | o   |     |     | i o |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

| ToyexampleoverZ |     |     | .   |     |     |     |     | InputsandOutputs: |     |     |     |     |     |     |     |
| --------------- | --- | --- | --- | --- | --- | --- | --- | ----------------- | --- | --- | --- | --- | --- | --- | --- |
25
|     |     |     |   |     |     |     |     | (cid:10) T(cid:48)(cid:11)A | (cid:10) T(cid:48)(cid:11)B |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --------------------------- | --------------------------- | --- | --- | --- | --- | --- | --- |
7 , ←HomCONV({(cid:104)T(cid:105)A,K},{(cid:104)T(cid:105)B,sk})
|     | (cid:20) 1 2 | 3 (cid:21) |     |     |            |                  |     |           |                                           |     |            |     |           |     |             |
| --- | ------------ | ---------- | --- | --- | ---------- | ---------------- | --- | --------- | ----------------------------------------- | --- | ---------- | --- | --------- | --- | ----------- |
| W=  |              | ,v=8⇒Wv≡ |     |     | (cid:2) 18 | 26 (cid:3) mod25 |     |           |                                           |     |            |     |           |     |             |
|     | 4 5          | 6          |     |     |            |                  |     |           |                                           |     |            |     |           |     |             |
|     |              |            |     |     |            |                  |     | such that | (cid:104)T(cid:105)A,(cid:104)T(cid:105)B |     | ∈ ZC ×H×W, | K ∈ | ZM ×C×h×h | and | T(cid:48) = |
|     |              |            | 9   |     |            |                  |     |           |                                           |     | p          |     | p         |     |             |
Conv2D(T,K;s)∈ZM×H(cid:48)×W(cid:48).
| CheetahevaluatesWvusingπw |     |     |     | andπi |     |     |     |                                             |     |     | p   |     |     |     |     |
| ------------------------- | --- | --- | --- | ----- | --- | --- | --- | ------------------------------------------- | --- | --- | --- | --- | --- | --- | --- |
|                           |     |     |     |       | .   |     |     | PublicParameters:pp=(HE.pp,pk,M,C,H,W,h,s). |     |     |     |     |     |     |     |
|                           |     |     |     | fc    | fc  |     |     |                                             |     |     |     |     |     |     |     |
• ShapemetaM,C,H,W,hsuchthatMCHW≤Nandh≤H,W,
πw(W)→wˆ=3X0+2X1+1X2+6X3+5X4+4X5∈A
| fc  |     |     |     |     |     |     | 8,25 | andstrides>0. |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | ---- | ------------- | --- | --- | --- | --- | --- | --- | --- |
πi (v)→vˆ=7X0+8X1+9X2∈A
fc 8,25 • SetH(cid:48)=(cid:98)H−h+s(cid:99),W(cid:48)=(cid:98)W−h+s(cid:99),andO=HW(MC−1)+
|     |     |     |     |                    |     |     |     |             |     | s   |     | s   |     |     |     |
| --- | --- | --- | --- | ------------------ | --- | --- | --- | ----------- | --- | --- | --- | --- | --- | --- | --- |
|     |     |     |     | ⇓wˆ·vˆmod(X8+1,25) |     |     |     | W(h−1)+h−1. |     |     |     |     |     |     |     |
wˆ·vˆ≡21X0+6X1+18X2+
|     |     |     |     |     |     |     |     |        |         |     |          |            | (cid:104)tˆ(cid:105)B | =πi ((cid:104)T(cid:105)B). |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ------ | ------- | --- | -------- | ---------- | --------------------- | --------------------------- | --- |
|     |     |     |     |     |     |     |     | 1: Bob | encodes | its | share as | polynomial |                       | conv                        |     |
4X3+284+26X5+13X6+4X7mod(X8+1,25) BobsendstheciphertextCT(cid:48)=RLWEN,q,p((cid:104)tˆ(cid:105)B)toAlice.
pk
⇓Extractneededcoefficients 2: Aliceencodesitsshareofinputtensorandthefilteraspoly-
|                                |     |     |     |     |     |     |     | nomials(cid:104)tˆ(cid:105)A=πi |     |      | ((cid:104)T(cid:105)A),kˆ=πw |                    | (K). |     |     |
| ------------------------------ | --- | --- | --- | --- | --- | --- | --- | ------------------------------- | --- | ---- | ---------------------------- | ------------------ | ---- | --- | --- |
| LWE(18)=Extract(RLWE(wˆ·vˆ),2) |     |     |     |     |     |     |     |                                 |     | conv |                              | conv               |      |     |     |
|                                |     |     |     |     |     |     |     | AlicesamplesR∈ZM                |     |      | ×H(cid:48)×W(cid:48)         |                    |      |     |     |
|                                |     |     |     |     |     |     |     | 3:                              |     |      | p                            | uniformlyatrandom. |      |     |     |
LWE(26)=Extract(RLWE(wˆ·vˆ),5)
|     |     |     |     |     |     |     |     | 4: On | receiving | the | RLWE ciphertext |     | CT(cid:48) from | Bob,Alice |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ----- | --------- | --- | --------------- | --- | --------------- | --------- | --- |
operatestoobtainCT=(CT(cid:48)(cid:1)(cid:104)tˆ(cid:105)A)(cid:2)kˆ.
Figure3:Toyexampleforπw andπi withN=8and p=25. [ExtractandRe-mask.]Foreachc(cid:48)∈[[M]],i(cid:48)∈[[H(cid:48)]]and
|     |     |     |     | fc  | fc  |     |     | 5:  |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
j(cid:48)∈[[W(cid:48)]],AlicefirstextractsaLWEciphertextct
|     |     |     |     |     |     |     |     |     |     |     |     |     |     | c(cid:48),i(cid:48),j(cid:48) | =   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ----------------------------- | --- |
Extract(CT,O−c(cid:48)CHW+i(cid:48)sW+j(cid:48)s)
|         |            |           |             |              |             |             |                  |     |     |     |     |     | andthen | re-masks |     |
| ------- | ---------- | --------- | ----------- | ------------ | ----------- | ----------- | ---------------- | --- | --- | --- | --- | --- | ------- | -------- | --- |
| ( n¯ an | d n ¯ ca n | b e c h o | s e n f r e | e ly a s p u | b l i c p a | r am e t er | s a s lo n g a s |     |     |     |     |     |         |          |     |
i o i t v ia c t (cid:48) = ct c(cid:48) ,i(cid:48), j(cid:48) (cid:12) R [c (cid:48), i(cid:48) , j(cid:48)]. Alicethen sendsthe
|     |     |     |     |     |     |     | (cid:45) |     | c(cid:48) | , i(cid:48), j(cid:48) |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | -------- | --- | --------- | ---------------------- | --- | --- | --- | --- | --- |
th e y s at i s fy t hi s c o n s tr a in t ) . Z er o - p a d d i n g i s us e d w h e n n i n¯ i c ip h er te x t s { ct (cid:48) } b a ck to B o b .
c(cid:48),i(cid:48),j(cid:48)
orn (cid:45)n¯.Thenweconvertthetaskofmatrixmultiplication
| o        | o   |                            |     |     |     |     |     | 6: AliceoutputsRastheshare(cid:104)T(cid:48)(cid:105)A. |     |     |     |     |     |     |     |
| -------- | --- | -------------------------- | --- | --- | --- | --- | --- | ------------------------------------------------------- | --- | --- | --- | --- | --- | --- | --- |
| inshapen | ×n  | tosubtasksofasmallersizen¯ |     |     |     | ×n¯ | .   |                                                         |     |     |     |     |     |     |     |
|          | i   | o                          |     |     |     | i   | o   | OnreceivingtheLWEciphertextsfromAlice,Bobcomputes       |     |     |     |     |     |     |     |
7:
|     |     |     |     |     |     |     |     | (cid:104)T(cid:48)(cid:105)B[c(cid:48),i(cid:48),j(cid:48)]=LWE− |     |     | 1(ct(cid:48) |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ---------------------------------------------------------------- | --- | --- | ------------ | --- | --- | --- | --- |
Theorem1 The protocol HomFC in Figure 2 realizes the )forallpositions(c(cid:48),i(cid:48),j(cid:48)).
|     |     |     |     |     |     |     |     |     |     |     | sk  | c(cid:48),i(cid:48),j(cid:48) |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ----------------------------- | --- | --- | --- |
ofFigure1aforF=Z
| idealfunctionalityF |     |     | FC  |     |     | p   | inpresence |     |     |     |     |     |     |     |     |
| ------------------- | --- | --- | --- | --- | --- | --- | ---------- | --- | --- | --- | --- | --- | --- | --- | --- |
ofasemi-honestadmissibleadversary. Figure4:ProposedSecureConvolutionProtocol(BasicVer)
WedefertheprooftoAppendixDduetothespacelimit.For
thecomplexity,Bobencryptsandsendsn(cid:48) RLWEciphertexts A directlygivesthe2-dimensionconvolutioninsomeof
|                                    |     |     |     |           | i   |                  |     | N,p                                      |     |     |     |     |     |     |     |
| ---------------------------------- | --- | --- | --- | --------- | --- | ---------------- | --- | ---------------------------------------- | --- | --- | --- | --- | --- | --- | --- |
| toAlice.Aliceoperateswithn(cid:48) |     |     |     | n(cid:48) |     |                  |     |                                          |     |     |     |     |     |     |     |
|                                    |     |     |     | o =O(n    | o n | i /N)homomorphic |     | thecoefficientsoftheresultingpolynomial. |     |     |     |     |     |     |     |
i
| multiplicationsandadditions.Alicesendsn |     |     |     |     |     | LWEciphertexts |     |     |     |     |     |     |     |           |     |
| --------------------------------------- | --- | --- | --- | --- | --- | -------------- | --- | --- | --- | --- | --- | --- | --- | --------- | --- |
|                                         |     |     |     |     |     | o              |     |     |     |     |     |     |     | πi (T),kˆ |     |
to Bob for decryption which can be compressed to about Proposition2 Given two polynomials tˆ = =
conv
+n(cid:48) π w (K ) ∈ A , th e co n vo lu t i o n T (cid:48) = C o n v 2 D (T , K ;s) ( 2)
| O((n | N)log | q)bitsusingtheoptimizationsin§5.2. |     |     |     |     |     | co nv    | N         | , p       |          |              |            |               |            |
| ---- | ----- | ---------------------------------- | --- | --- | --- | --- | --- | -------- | --------- | --------- | -------- | ------------ | ---------- | ------------- | ---------- |
| o    | o     | 2                                  |     |     |     |     |     |          |           |           |          |              |            |               | tˆ(cid:48) |
|      |       |                                    |     |     |     |     |     | ca n b e | e va lu a | t e d b y | th e p o | l y n o m ia | l m u l ti | p lic at i on | =          |
tˆ·kˆ
|     |                           |     |     |     |     |     |     | over                                     | the ring    | A   | . For  | all positions |                           | (c(cid:48),i(cid:48),j(cid:48)) | of T(cid:48), |
| --- | ------------------------- | --- | --- | --- | --- | --- | --- | ---------------------------------------- | ----------- | --- | ------ | ------------- | ------------------------- | ------------------------------- | ------------- |
| 3.2 | TwoDimensionalConvolution |     |     |     |     |     |     |                                          |             | N,p |        |               |                           |                                 |               |
|     |                           |     |     |     |     |     |     | T(cid:48)[c(cid:48),i(cid:48),j(cid:48)] | is computed |     | in the | coefficient   | tˆ(cid:48)[O−c(cid:48)CHW |                                 | +             |
i(cid:48)sW+j(cid:48)s]whereO=HW(MC−1)+W(h−1)+h−1.
| We now | present | how | to evaluate | the | two | dimensional | con- |     |     |     |     |     |     |     |     |
| ------ | ------- | --- | ----------- | --- | --- | ----------- | ---- | --- | --- | --- | --- | --- | --- | --- | --- |
volution(2)usingpolynomialarithmeticovertheringA
N,p .
Similarly,AlicecanapplytheExtract(·)functiontoprevent
| Considerthemostsimplecaseof(2)suchthatH=W |     |     |     |     |     |     | =hand |     |     |     |     |     |     |     |     |
| ----------------------------------------- | --- | --- | --- | --- | --- | --- | ----- | --- | --- | --- | --- | --- | --- | --- | --- |
possibleleakage.Wefirstpresentthebasicversionofourse-
M=1,i.e.,theinputtensorhasthesameshapeastheconvo-
cureconvolutionprotocolinFigure4whichdemands“small
lutionkernel.Thenthecomputationin(2)becomesaninner
|     |     |     |     |     |     |     |     | enoughtensors”i.e.,MCHW |     |     | ≤N. |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ----------------------- | --- | --- | --- | --- | --- | --- | --- |
productoftwoflattenvectorsbyconcatenatingTandKrow-
by-rowandchannel-by-channel.Forgeneralcases,wecan
|     |     |     |     |     |     |     |     | Theorem2 | The | protocol | HomCONV |     | in Figure | 4 realizes |     |
| --- | --- | --- | --- | --- | --- | --- | --- | -------- | --- | -------- | ------- | --- | --------- | ---------- | --- |
viewthecomputationof2-dimensionconvolutionasabatch theidealfunctionalityF ofFigure1bforF=Z and
|     |     |     |     |     |     |     |     |     |     |     | CONV |     |     |     | p   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---- | --- | --- | --- | --- |
ofinnerproductsofh2values.Wenowgivethedefinitionsof
|               |          |            |                   |      |                  |     |           | for inputs           | that | MCHW | ≤N  | in presence | of  | a semi-honest |     |
| ------------- | -------- | ---------- | ----------------- | ---- | ---------------- | --- | --------- | -------------------- | ---- | ---- | --- | ----------- | --- | ------------- | --- |
| πi            | :ZC ×H×W | (cid:55)→A | andπw             | :ZM  | ×C×h×h(cid:55)→A |     |           |                      |      |      |     |             |     |               |     |
|               |          |            | N,p               |      |                  |     | N,p .Here | admissibleadversary. |      |      |     |             |     |               |     |
| conv          | p        |            |                   | conv | p                |     |           |                      |      |      |     |             |     |               |     |
| werequireMCHW |          |            | ≤N forsimplicity. |      |                  |     |           |                      |      |      |     |             |     |               |     |
WedeferthecorrectnessandsecurityproofstoAppendixD.
tˆ=πi
|     | (T)st.tˆ[cHW+iW+j]=T[c,i,j] |     |     |     |     |     | (5) |     |     |     |     |     |     |     |     |
| --- | --------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
conv
kˆ=πw (K)st.kˆ[O−c(cid:48)CHW−cHW−lW−l(cid:48)]=K[c(cid:48),c,l,l(cid:48)], 3.2.1 OntheCasesofLargeTensors
conv
where O=HW(MC−1)+W(h−1)+h−1,andallother Weneedtopartitionlargeinputtensorsandkernelssothat
coefficientsoftˆandkˆ aresetto0.Themultiplicationtˆ·kˆ∈ each of the smaller blocks can be fit into one polynomial

|     |     |     | 0 1 2 3 |     | 0 1 |     | InputsandOutputs: |                             |                             |     |                   |                     |     |                   |
| --- | --- | --- | ------- | --- | --- | --- | ----------------- | --------------------------- | --------------------------- | --- | ----------------- | ------------------- | --- | ----------------- |
|     |     |     | 4 5 6 7 |     | 4 5 |     |                   |                             |                             |     |                   |                     |     |                   |
|     |     |     |         |     |     |     |                   | (cid:10) T(cid:48)(cid:11)A | (cid:10) T(cid:48)(cid:11)B |     | (cid:16)(cid:110) | (cid:111) (cid:110) |     | (cid:111)(cid:17) |
8 9 10 11 8 9 , ←HomBN (cid:104)T(cid:105)A,µ,θ , (cid:104)T(cid:105)B,sk
|     |     |     | 12 13 14 15 |     | 12 13 |     |     |     |     |     |     |     |     |     |
| --- | --- | --- | ----------- | --- | ----- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
s.t.(cid:104)T(cid:105)A,(cid:104)T(cid:105)B∈ZC×H×W,µ,θ∈ZCandT(cid:48)=BN(T;µ,θ).
|     |     |     |         |     |     |     |                                       |                    | p                         |       |       | p                            |     |            |
| --- | --- | --- | ------- | --- | --- | --- | ------------------------------------- | ------------------ | ------------------------- | ----- | ----- | ---------------------------- | --- | ---------- |
|     |     |     |         |     |     |     | PublicParameters:pp=(HE.pp,pk,C,H,W,C |                    |                           |       |       |                              | ,H  | ,W ).      |
|     |     |     |         |     |     |     |                                       |                    |                           |       |       |                              | w w | w          |
|     |     |     |         |     |     |     | •                                     | The partition      | window                    | sizes | 0<C   | ≤C,0<H                       | ≤H  | and        |
|     |     |     |         |     |     |     |                                       |                    |                           |       |       | w                            | w   |            |
|     |     |     |         |     |     |     |                                       | 0<W ≤W             | suchthatC                 |       | 2H W  | ≤N.                          |     |            |
|     |     |     |         |     |     |     |                                       | w                  |                           |       | w w w |                              |     |            |
|     |     |     | 0 1 2 3 |     | 0 1 |     |                                       |                    |                           |       |       |                              |     |            |
|     |     |     |         |     |     |     | •                                     | Letd =(cid:100)C/C | (cid:101),dH=(cid:100)H/H |       |       | (cid:101)anddW =(cid:100)W/W |     | (cid:101). |
|     |     |     | 4 5 6 7 |     | 4 5 |     |                                       | C                  | w                         |       | w     |                              | w   |            |
(cid:10) (cid:11)B ∈
|     |     |     |     |     |     |     | 1:  | Bobpartitionsitssharetensorintosub-blocks |                                |     |     |     | T   | γ,α,β |
| --- | --- | --- | --- | --- | --- | --- | --- | ----------------------------------------- | ------------------------------ | --- | --- | --- | --- | ----- |
|     |     |     |     |     |     |     |     | ZC pw×Hw×Ww                               | (withzero-paddingifnecessary). |     |     |     |     |       |
F ig ur e 5 : P a rti tio n in g t he in pu t ten so r a lo ng th e H -axi s and W - (cid:10) (cid:11)B
|     |     |     |     |     |     |     | 2:  | Bobthenencodesthesub-blocksaspolynomials |     |     |     |     | tˆ  | =   |
| --- | --- | --- | --- | --- | --- | --- | --- | ---------------------------------------- | --- | --- | --- | --- | --- | --- |
ax is w h e r e N = 1 6 , C = 1 ,H , W = 5 , h = 2, a n dH , W = 4 . γ,α,β
|     |     |     |     |     |     | w w |     | πi (cid:10) | (cid:11)B |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ----------- | --------- | --- | --- | --- | --- | --- |
Digitsrepresentthecoefficientindicesinanencode dpo lyno- ( T γ,α,β )forγ∈[[d C ]],α∈[[dH]]andβ∈[[dW]].Bob
bn
|                                    |     |     |     |     |     |     |     | thensends{CT(cid:48) |     | =RLWEN |     | ,q,p( (cid:10) tˆ (cid:11)B | )}toAlice. |     |
| ---------------------------------- | --- | --- | --- | --- | --- | --- | --- | -------------------- | --- | ------ | --- | --------------------------- | ---------- | --- |
| mial.Thedashedpartsarezeropadding. |     |     |     |     |     |     |     |                      |     | γ,α,β  | pk  | γ,α,β                       |            |     |
3: Alicepartitionsandencodesitsinputtensorandthescaling
|     |     |     |     |     |     |     |     |                       |     |     | (cid:10) (cid:11)A | (cid:10) | (cid:11)A |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --------------------- | --- | --- | ------------------ | -------- | --------- | --- |
|     |     |     |     |     |     |     |     | vectoraspolynomials   |     |     | tˆ                 | =πi ( T  | )andaˆγ   | =   |
|     |     |     |     |     |     |     |     |                       |     |     | γ,α,β              | bn γ,α,β |           |     |
|     |     |     |     |     |     |     |     | πw (µ ),respectively. |     |     |                    |          |           |     |
|     |     |     |     |     |     |     |     | bn γ                  |     |     |                    |          |           |     |
|     |     |     |     |     |     |     |     | AlicesamplesR∈ZC      |     |     | ×H×W               |          |           |     |
|     |     |     |     |     |     |     | 4:  |                       |     |     | uniformlyatrandom. |          |           |     |
p
in A . Particularly, we define the size of partition win- 5: On receiving the ciphertexts {CT(cid:48) } from Bob,Alice
|     | N,p |     |     |     |     |     |     |     |     |     |     | γ,α,β |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ----- | --- | --- |
d o w f o r th e (M ,C , H , W )- ax i s a s M ,C , H a n d W , r e - (cid:1)(cid:10) (cid:11)A
|          |             |        |                      | w      | w w            | w             |     | operatesCT |       | =(CT(cid:48) |       | tˆ )(cid:2)aˆγforγ∈[[d |     | ]], |
| -------- | ----------- | ------ | -------------------- | ------ | -------------- | ------------- | --- | ---------- | ----- | ------------ | ----- | ---------------------- | --- | --- |
|          |             |        |                      |        |                |               |     |            | γ,α,β |              | γ,α,β | γ,α,β                  |     | C   |
| sp e cti | v e ly . Th | e s iz | e o f th e p a rt it | io n w | in d o w s c a | n b e c h o - |     |            |       |              |       |                        |     |     |
α∈[[dH]]andβ∈[[dW]].
sen freelyaslongastheysatisfythefollowingconstraints:
|     |     |     |     |     |     |     | 6:  | [Extract | and Re-mask.] |     | For | each c∈[[C]],i∈[[H]] |     | and |
| --- | --- | --- | --- | --- | --- | --- | --- | -------- | ------------- | --- | --- | -------------------- | --- | --- |
0 < M w ≤ M, 0 <C w ≤C, h ≤ H w ≤ H, h ≤W w ≤W j ∈[[W]], Alice first extracts a LWE ciphertext ctc,i,j =
and M C H W ≤ N. For instance, in our experiments, Extract(CT c(cid:48),i(cid:48),j(cid:48),cCHW +cHW +iH+ j), where c(cid:48) =
|     | w w | w w |     |     |     |     |     |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
to minimize the number of ciphertexts sent by Bob, we cmodd C,i(cid:48) =imodH j(cid:48) = jmodW.
|     |     |     |     |     |     |     |     |                                    |     |     | and |                   | Then | Bob re- |
| --- | --- | --- | --- | --- | --- | --- | --- | ---------------------------------- | --- | --- | --- | ----------------- | ---- | ------- |
|     |     |     |     |     |     |     |     | maskstheseciphertextsviact(cid:48) |     |     |     | (cid:12)R[c,i,j]. |      |         |
choose the window sizes H w and W w that minimize the =ctc,i,j
c,i,j
product(cid:100) C (cid:101)·(cid:100) H − h + 1 (cid:101)·(cid:100) W − h + 1 (cid:101).WhenH and 7: Alicesendstheciphertexts{ct(cid:48) }backtoBob,andAlice
|     | (cid:98)N/(H | wWw)(cid:99) | H − h + 1 | W + | h − 1 | w   |     |     |     |     |     | c,i,j |     |     |
| --- | ------------ | ------------ | --------- | --- | ----- | --- | --- | --- | --- | --- | --- | ----- | --- | --- |
w w ouputs(cid:104)T(cid:48)(cid:105)Aas(cid:104)T(cid:48)(cid:105)A[c,i,j]=R[c,i,j]+θ[c]mod
W w are specified, the partition window sizes along the C- p.
axis and M-axis is C =min(C,(cid:98)N/(H W )(cid:99)) and M = 8: OnreceivingtheLWEciphertextsfromAlice,Bobouputs
|     |     |     | w   |     | w w | w   |     |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
min(M,(cid:98)N/(C H W )(cid:99)),respectively. (cid:104)T(cid:48)(cid:105)Bas(cid:104)T(cid:48)(cid:105)B[c,i,j]=LWE− 1(ct(cid:48)
|     |     | w w | w   |     |     |     |     |     |     |     | sk  | c,i,j ). |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | -------- | --- | --- |
Bysplittingthebigtensorandkernelintosmallerblocks
Figure6:ProposedSecureBatchNormalizationProtocol
andzero-paddingthemarginblocks,wecanapply(5)onthe
correspondingpairofsubtensorandsubkernel.Wedemon-
stratewhysuchpartitionscanworkcorrectly.Fromthedefi-
3.2.2 HomCONV(FullProtocol)
nitionin(2),theconvolutionalongtheM-axisisindependent
ThefullversionofHomCONVisgiveninAppendixCdue
foreachsubkernel,andthuswecanequallysplittheM-axis
intod =(cid:100) M (cid:101)groupsandeachofthemcontainsM tothespacelimitbutwestatethecomplexityofHomCONV.
|        | M     |                                         |     |     |     | w sub- |                                             |     |     |     |     |     |     |     |
| ------ | ----- | --------------------------------------- | --- | --- | --- | ------ | ------------------------------------------- | --- | --- | --- | --- | --- | --- | --- |
|        | M     | w                                       |     |     |     |        | InHomCONV,BobsendsO(CHW/N)RLWEciphertextsto |     |     |     |     |     |     |     |
| kernel | s.Sim | il arly,theconvolutionalongtheC-axisreq |     |     |     | uires  |                                             |     |     |     |     |     |     |     |
extra additions which are supported by HEs. Thus we can AlicewhichareaboutO(2CHWlog q)bits.Aliceoperates
2
O(MCHW/N)homomorphicadditionsandmultiplications.
safelypartitionalongtheC-axiswithoutoverlappingtoo.
|     |     |     |     |     |     |     | Alice | sends | backO( | M H(cid:48)W(cid:48)) | LWE | ciphertexts | to  | Bobfor |
| --- | --- | --- | --- | --- | --- | --- | ----- | ----- | ------ | --------------------- | --- | ----------- | --- | ------ |
Mw
Whenthekernelsizeh>1,weneedtotakeextracarefor decryption. The computation complexity of HomCONV is
independentwiththekernelsizehwheretheprevioussecure
| the partition |     | overthe | H-axis andW-axis. |     | Thatis,we | need |     |     |     |     |     |     |     |     |
| ------------- | --- | ------- | ----------------- | --- | --------- | ---- | --- | --- | --- | --- | --- | --- | --- | --- |
to make sure that the stride window is not split into two convolutionprotocols[10,34,39]scalequadraticallywithh.
adjacentpartitions.Specifically,wepartitionalongtheH-axis
|                |     |        | H−h+1                    |     | =(cid:100)W−h+1(cid:101)blocks, |       |     |                    |     |     |     |     |     |     |
| -------------- | --- | ------ | ------------------------ | --- | ------------------------------- | ----- | --- | ------------------ | --- | --- | --- | --- | --- | --- |
| andW-axisintod |     |        | =(cid:100) (cid:101)andd |     |                                 |       |     |                    |     |     |     |     |     |     |
|                |     | H      | Hw−h+1                   | W   | Ww−h+1                          |       | 3.3 | BatchNormalization |     |     |     |     |     |     |
| respectively.  |     | Forthe | sub-blockindexedby       |     | (α∈[[d                          | ]],β∈ |     |                    |     |     |     |     |     |     |
H
[[d ]]),itcontainsexactH continuousrowsthatstartsfrom The batch normalization (3) can be evaluated using scalar-
| W   |     |     | w   |     |     |     |     |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
theα(H −h+1)-throw,andexactW continuouscolumns polynomialmultiplicationsbymappingeachchannelofthe
|     | w   |     |     | w   |     |     |     |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
thatstartsfromtheβ(W w −h+1)-thcolumnofthebigtensor tensor to polynomials. This idea will lead to a secure BN
T.Whenh>1,thereareoverlappingbetweenadjacentblocks. protocolofacommunicationcostofO(C(cid:100)HW/N(cid:101))cipher-
WegiveanexampleofthiscaseinFigure5. texts.Wecanreducethiscommunicationcostby“stacking”

Parameters:Bitwidth(cid:96)>0. Table2:CommunicationcomplexityofvariousOTprotocols
Computation:Oninputx∈Z fromAliceandinputy∈Z usedinCrypTFlow2andCheetah.CheetahusesVOLE-style
fromBob,computeb=1{x> 2 y (cid:96) }.SampleabitrfromZ un 2 i (cid:96) - OTfortheunderlyingcallsto (cid:0)2(cid:1) -ROT .
2 1 λ
formlyatrandom.
Return:rtoAliceandb⊕rtoBob.
Communication(bits)
Function
(a)IdealFunctionalityF(cid:96) CrypTFlow2 Cheetah
Mill
Parameters:Bitwidth(cid:96)>0andfixed-pointprecision0< f <(cid:96).
(cid:0)2
1
(cid:1)
-OT
(cid:96)
λ+2(cid:96) 2(cid:96)+1
Computation:Oninput(cid:104)x(cid:105)A 2(cid:96) fromAliceandinput(cid:104)x(cid:105)B (cid:96) from (cid:0)2 1 (cid:1) -COT (cid:96) λ+(cid:96) (cid:96)+1
B
R
o
et
b
u
,
r
c
n
o
:
m
r
pu
to
te
A
x
l
(cid:48)
i
=
ce
(cid:98)
a
x
n
/
d
2
x
f
(cid:48)
(cid:99)
−
.S
r
a
∈
mp
Z
lea
to
un
B
i
o
fo
b
r
.
mvaluerfromZ 2(cid:96) . (cid:0)n
1
(cid:1) -OT
(cid:96)
(n≥3) 2λ+n(cid:96) n(cid:96)+log
2
n
2(cid:96)
(b)IdealFunctionalityF tr (cid:96) u , n f c Table3:Communicationcomplexityofmillionaires’proto-
colsof(cid:96)-bitintegers.
Figure7:IdealFunctionalitiesofNon-linearFunctions
Millionaires’Protocol Communication(bits)
multiplechannelsofthetensorintoasinglepolynomial.For CrypTFlow2(m=4,IKNP, (cid:0)n(cid:1) -OT) <λ(cid:96)+14(cid:96)
example,whenC2HW ≤N,we can even put all the chan- 1
Naive(m=1,VOLE,
(cid:0)2(cid:1)
-ROT) <16(cid:96)
nels into one polynomial. We now give the definitions of 1
πi bn :ZC p ×H×W (cid:55)→A N,p and πw bn :ZC p (cid:55)→A N,p . Here we de- Cheetah(m=4,VOLE, (cid:0)2 1 (cid:1) -ROT) <11(cid:96)
mandC2HW ≤N forsimplicity.
tˆ=πi
bn
(T)s.t.tˆ[cCHW+iH+j]=T[c,i,j] (cid:0)2(cid:1)
-ROT ,whereasCrypTFlow2implementsitwiththeIKNP-
1 λ
aˆ=πw(α)s.t.aˆ[cHW]=α[c]
style OT extension proposed in [35]. Due to the usage of
bn
VOLE-styleOT,ourcallsto
(cid:0)2(cid:1)
-ROT enjoysalmost0amor-
wherec∈[[C]],i∈[[H]]and j∈[[W]].Allothercoefficients 1 λ
tized communication cost. We provide a brief comparison
oftˆandaˆaresettozero. Thepolynomialproducttˆ(cid:48)=tˆ·aˆ
of these two approaches in Table 2. When n and the mes-
givesthemultiplicationpartof(3)insomeofcoefficientsof
sagelength(cid:96)aresmall,ourapproachdemonstratesprominent
tˆ(cid:48).Thatistˆ(cid:48)[cCHW+cHW+iH+j]equalstoT[c,i,j]α[c]
advantage,whichisindeedthecaseinallprotocolsusedin
forall(c,i,j)position.WhenC2HW >N,wecanfirstpar-
neuralnetworkinference(usually,n≤16,(cid:96)≤2).
tition T into sub-blocks in a shape ofC ×H ×W such
w w w
thatC2H W ≤N.Sinceeachchannelisproceedindepen-
w w w
dentlyintheBNcomputation,wecanjustapplythemapping 4.1 LeanerandBetterMillionaires’Protocol
functionsπi ,πw tothesub-blocksofT.
bn bn Millionaires’ protocol for comparing two integers (x,y ∈
Theorem3 The protocol HomBN in Figure 6 realizes the
{0,1}(cid:96))isthecorebuildingblockofalmosteverynon-linear
idealfunctionalityF BN ofFigure1cforthefieldF=Z p in layer,suchasReLU,truncation,andpooling.LetF AND denote
presenceofasemi-honestadmissibleadversary. thefunctionalitythatacceptsbooleansharesofxandyandre-
turnsbooleansharesofx∧y(protocoldetailsinAppendixE).
WedefertheprooftoAppendixDduetothespacelimit.For Webrieflyrecallthehigh-levelintuitionofthemillionaires’
thecomplexity,BobencryptsandsendsO(CHW/N)RLWE protocolin[46]:
ciphertexts to Alice. Alice operates with O(CHW/N) ho-
momorphicoperations.Finally,AlicesendsO(CHW)LWE 1. Eachpartyparsesitsown(cid:96)-bitinputassmallerblocksof
ciphertextstoBobfordecryption. mbits.Letx j andy j denotethe j-thblockofP 0 andP 1 ,
respectively.Twopartiesinvoke
(cid:0)2m(cid:1)
-OT tocomputea
1 1
booleanshareoflt =1{x <y }(similarinvocation
4 Optimized 2PC Protocols of Non-Linear j j j
foreq =1{x =y }).
Functions j j j
2. TwopartiesuseF tocombinetheformeroutputsina
AND
Fornon-linearcomputation,[46]presentsvariousprotocols treeevaluation(ofdepthlog((cid:96)/m))withtheobservation:
thataretailoredtobehighlyefficientonIKNP-styleOTex- 1{x < y} = 1{x < y }⊕(1{x = y }∧1{x < y }),
1 1 1 1 0 0
tension.Inthissection,weshowthattheirprotocolscanbe wherex=x ||x andy=y ||y .
1 0 1 0
simplifiedandoptimizedonVOLE-styleOTextension.
Throughoutthissection,wemakeuseof
(cid:0)2(cid:1)
-OT ,
(cid:0)2(cid:1)
-COT Instage2,[46]presentsvariousoptimizationstorealizeF
and
(cid:0)n(cid:1)
-OT .Weinstantiate
(cid:0)n(cid:1)
-OT withth
1
ealgo
(cid:96)
rith
1
mpro
(cid:96)
- efficientlyinthecontextofIKNP-styleOTextension,suc
A
h
N
a
D
s
posed
1
by N
(cid:96)
aor and Pinkas [
1
44] b
(cid:96)
y using log n calls to using
(cid:0)16(cid:1)
-OT togeneratetwobeavertriplesand
(cid:0)8(cid:1)
-OT to
2 1 2 1 2

|     |     |     |     |     |     |     |     |     |     |     |     |     | (cid:16) | (cid:17) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | -------- | -------- |
I n p u ts a n d O u tp u ts: (cid:104) z(cid:105)A , (cid:104) z(cid:105) B ← T run c ( (cid:104)x (cid:105) A ,(cid:104)x(cid:105)B ,f)such A B x(cid:105)A B
2(cid:96) 2(cid:96) 2(cid:96) 2(cid:96) I n p u t s a n d O utp u ts : (cid:104) z (cid:105) , (cid:104) z (cid:105) ← T ru nc m s b (cid:104) , (cid:104)x(cid:105) , f
|     | Z   |     |     |     |     |     |     |     |     | 2(cid:96) | 2(cid:96) |     |     | 2 (cid:96) 2(cid:96) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --------- | --------- | --- | --- | -------------------- |
th a t x ∈ 2 (cid:96) , a nd z = x (cid:29) f o r z = (x (cid:29) f ) − 1 . su c h t h a t x ∈ Z , ms b ( x ) = 0 , a n d z= x (cid:29) f o r z = ( x (cid:29) f ) − 1.
2(cid:96)
| 1:  | Alice | and Bob | call the | millionaires’ |     | protocol: |     |     |     |     |     |     |     |     |
| --- | ----- | ------- | -------- | ------------- | --- | --------- | --- | --- | --- | --- | --- | --- | --- | --- |
Alicesamples(cid:104)w(cid:105)A
((cid:104)w(cid:105)A,(cid:104)w(cid:105)B)=Mill(cid:96)((cid:104)x(cid:105)A,2(cid:96)−1−(cid:104)x(cid:105)B). 1: 2 ←R{0,1}.
|     | 2     | 2              |             |     |     |             |     |                                              |     |     |                           |                            |                         |        |
| --- | ----- | -------------- | ----------- | --- | --- | ----------- | --- | -------------------------------------------- | --- | --- | ------------------------- | -------------------------- | ----------------------- | ------ |
|     |       |                |             |     | F2f |             |     | 2: Ifmsb((cid:104)x(cid:105)A)=0,Alicesets(s |     |     |                           | ,s )=((cid:104)w(cid:105)A | ,1⊕(cid:104)w(cid:105)A | );oth- |
| 2:  | Alice | and Bob invoke | an instance |     | of  | with inputs |     |                                              |     |     | 0                         | 1                          | 2                       | 2      |
|     |       |                |             |     | B2A |             |     |                                              |     |     | )=(1⊕(cid:104)w(cid:105)A |                            | ,1⊕(cid:104)w(cid:105)A |        |
((cid:104)w(cid:105)A,(cid:104)w(cid:105)B)andlearn((cid:104)w(cid:105)A ,(cid:104)w(cid:105)B ). erwise,Alicesets(s 0 ,s 1 2 2 ).
|     | 2   | 2   | 2   | f 2 f |     |     |     |     |     | (cid:0)2 | (cid:1) |     |     |     |
| --- | --- | --- | --- | ----- | --- | --- | --- | --- | --- | -------- | ------- | --- | --- | --- |
(cid:105)A x(cid:105)A (cid:105)A 3: A l i c e a n d Bo b in v o k e - O T , w h e r e A l ic e in p ut s m e ss a g e s
3: A li c e c o m p ut e s (cid:104) z = ( (cid:104) (cid:29) f ) − (cid:104)w ·2(cid:96)−f.Bobcom- 1 1
|     |     |     |     |     | 2f  |     |     | ( s , s | )   |     |     | ( (cid:104) x(cid:105) | B ) | (cid:104) w (cid:105) B |
| --- | --- | --- | --- | --- | --- | --- | --- | ------- | --- | --- | --- | ---------------------- | --- | ----------------------- |
pu t e s (cid:104)z (cid:105) B = ( (cid:104) x (cid:105) B (cid:29) f ) − (cid:104) w (cid:105)B · 2 (cid:96) − f. 0 1 a nd B ob i n p u ts a c h o i c e m s b .B o b l ea rn s 2
2f
asitsoutput.
|                                                      |     |     |     |     |     |     |     | 4: Alice                                                                 | and Bob | invoke | an instance | of                    | F2f | with inputs |
| ---------------------------------------------------- | --- | --- | --- | --- | --- | --- | --- | ------------------------------------------------------------------------ | ------- | ------ | ----------- | --------------------- | --- | ----------- |
| Figure8:ProposedOne-BitApproximateTruncationProtocol |     |     |     |     |     |     |     |                                                                          |         |        |             |                       | B2A |             |
|                                                      |     |     |     |     |     |     |     | ((cid:104)w(cid:105)A,(cid:104)w(cid:105)B)andlearn((cid:104)w(cid:105)A |         |        |             | ,(cid:104)w(cid:105)B |     |             |
| intheF2f                                             |     |     |     |     |     |     |     | 2                                                                        | 2       |        | 2f          | 2f ).                 |     |             |
-hybridmodel.
B2A 5: Alicecomputes(cid:104)z(cid:105)A=((cid:104)x(cid:105)A(cid:29) f)−(cid:104)w(cid:105)A ·2(cid:96)−f.Bobcom-
2f
|     |     |     |     |     |     |     |     | putes(cid:104)z(cid:105)B=((cid:104)x(cid:105)B(cid:29) |     | f)−(cid:104)w(cid:105)B |     | ·2(cid:96)−f. |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ------------------------------------------------------- | --- | ----------------------- | --- | ------------- | --- | --- |
2f
generatecorrelatedtriples.However,inCheetah,theseareless
(cid:0)2(cid:1) Figure9:ProposedTruncationProtocolwithInputMSB=0
| efficientthanusing |     |     | -ROT togeneratethebeavertriples[3]. |     |     |     |          |     |     |     |     |     |     |     |
| ------------------ | --- | --- | ----------------------------------- | --- | --- | --- | -------- | --- | --- | --- | --- | --- | --- | --- |
|                    |     | 1   | 1                                   |     |     |     | intheF2f |     |     |     |     |     |     |     |
-hybridmodel.
| Nevertheless,theirinsight |     |     | in stage | 1 to | start | working with |     | B2A |     |     |     |     |     |     |
| ------------------------- | --- | --- | -------- | ---- | ----- | ------------ | --- | --- | --- | --- | --- | --- | --- | --- |
m-bitblocksremainsimportanttogreatlyreducethenumber
ofANDgatescomparedtoanaiveapproachofusinganeval-
|     |     |     |     |     |     |     | c be | one-bit | integer | 0 or | 1. We | have: | (x (cid:29) | f)+(x (cid:29) |
| --- | --- | --- | --- | --- | --- | --- | ---- | ------- | ------- | ---- | ----- | ----- | ----------- | -------------- |
uation tree ofdepthlog(cid:96). Wecompare thecommunication 0 1
|     |     |     |     |     |     |     | f)−w·2(cid:96)=(x(cid:29) |     | f)−c. |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | ------------------------- | --- | ----- | --- | --- | --- | --- | --- |
complexityofthethreeapproachesinTable3.Wereusethe
millionaires’protocolflowfromCrypTFlow2,butreplacethe
Proof2 ThepropositionfollowsfromCorollary4.2in[46].
| underlyingF |     | implementationwithouraforementionedso- |     |     |     |     |                                                  |     |     |     |     |     |     |     |
| ----------- | --- | -------------------------------------- | --- | --- | --- | --- | ------------------------------------------------ | --- | --- | --- | --- | --- | --- | --- |
|             |     | AND                                    |     |     |     |     | First,wdenoteswhetherthesumoftwoshareswraparound |     |     |     |     |     |     |     |
lution.Let((cid:104)m(cid:105)A,(cid:104)m(cid:105)B)=Mill(cid:96)(x,y)denotethemillionaires’
|     |     | 2 2 |     |     |     |     | 2(cid:96). |             |      |          |               |     |            |     |
| --- | --- | --- | --- | --- | --- | --- | ---------- | ----------- | ---- | -------- | ------------- | --- | ---------- | --- |
|     |     |     |     |     |     |     |            | If so,there | will | be large | errorforlocal |     | truncation | and |
protocolwhereAlice’sinputisx,Bob’sinputisy,andthey
|     |     |     |     |     |     |     | it should | be  | corrected | by  | subtracting | 2(cid:96). | c comes | from a |
| --- | --- | --- | --- | --- | --- | --- | --------- | --- | --------- | --- | ----------- | ---------- | ------- | ------ |
receivebooleansharesasoutput:(cid:104)m(cid:105)A⊕(cid:104)m(cid:105)B=1{x>y}.
|     |     |     |     | 2   | 2   |     | probabilisticlast-biterrorthatisdecidedbywhetherthesum |     |     |     |      |                |     |         |
| --- | --- | --- | --- | --- | --- | --- | ------------------------------------------------------ | --- | --- | --- | ---- | -------------- | --- | ------- |
|     |     |     |     |     |     |     |                                                        |     |     |     |      | wrapsaround2f. |     | (cid:4) |
|     |     |     |     |     |     |     | ofleastsignificantsbitsofx                             |     |     |     | andx |                |     |         |
|     |     |     |     |     |     |     |                                                        |     |     |     | 0    | 1              |     |         |
4.2 ApproximateTruncation
LetF2f
denotethefunctionalitythatacceptsbooleanshares
B2A
Infixed-pointcomputation,truncationisanecessaryproce- ofx∈{0,1} andreturns arithmetic shares ofx in Z . We
2f
dure to maintain the precision after multiplication. CrypT- provideanimplementationofF2f
inAppendixE.Theone-
| Flow2proposesfaithfultruncationthatrealizesthefunction- |     |     |     |     |     |     |     |     |     |     | B2A |     |     |     |
| ------------------------------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
bitapproximatetruncationprotocolisprovidedinFigure8.
(cid:96),f
| alityF |     | (Figure7b). | Weobservethatlargeoverheadin |     |     |     |     |     |     |     |     |     |     |     |
| ------ | --- | ----------- | ---------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
Trunc
theprotocolcanberemovedinneuralnetworkinference.
4.2.2 ApproximateTruncationwithKnownMSB
Aspointedoutby[45],2PCprotocolscouldbedesignedin
4.2.1 One-BitApproximateTruncation
|     |     |     |     |     |     |     | a far | more | efficient | way when | the | MSB | of the | inputs are |
| --- | --- | --- | --- | --- | --- | --- | ----- | ---- | --------- | -------- | --- | --- | ------ | ---------- |
Inpriorworks[41–43],localtruncationisusedtoapproximate known. Inthesecases,truncation canbefurtheroptimized
F (cid:96),f ,whichleadstobothalargeerrorwithsmallprobability tobeacheapoperation.Weconsiderthecaseofourone-bit
Trunc
approximatetruncationwhenMSBiszero(e.g.,afterReLU),
andalast-bitsmallerrorwith1/2probability.CrypTFlow2
correctsboththeseerrors,resultinginaheavyfaithfultrunca- andgivethecorrespondingprotocoldetailsinFigure9.When
tionprotocol.Indeed,thelargeerrordestroystheresult,and MSBisknown,computingbooleansharesofthewrap-around
|     |     |     |     |     |     |     | bitwcanbeaccomplishedwithasinglecallto |     |     |     |     |     | (cid:0)2 | (cid:1) |
| --- | --- | --- | --- | --- | --- | --- | -------------------------------------- | --- | --- | --- | --- | --- | -------- | ------- |
inpractice,theprobabilityisactuallynon-negligiblewhen -OT 1 instead
1
(cid:96)≤64,whichisthecaseinthiswork.Nonetheless,asshown ofthe expensive Mill protocol. Indeed,when MSB is zero,
|             |     |                |       |          |        |             | w=msb((cid:104)x(cid:105)A)∨msb((cid:104)x(cid:105)B). |     |     |     | Asimilarprotocolcanalsobe |     |     |     |
| ----------- | --- | -------------- | ----- | -------- | ------ | ----------- | ------------------------------------------------------ | --- | --- | --- | ------------------------- | --- | --- | --- |
| by [15],the |     | last-bit small | error | does not | affect | the quality |                                                        |     |     |     |                           |     |     |     |
derivedwhenMSBisoneandw=msb((cid:104)x(cid:105)A)∧msb((cid:104)x(cid:105)B).
ofpredictionmodelsinmachinelearningwhichwealsoex-
perimentallyverifyinaconcreteneuralnetwork(see§6.4).
Weobservethatbyremovingtheconstraintofcorrectingthe
4.2.3 CommunicationComplexity
last-biterror,thetruncationprotocolcanbemadefarmore
|     |     |     |     |     |     |     | We  | provide | a comparison |     | of communication |     |     | complexity |
| --- | --- | --- | --- | --- | --- | --- | --- | ------- | ------------ | --- | ---------------- | --- | --- | ---------- |
lightweight,providingsignificantimprovementincommuni-
cationandcomputation. amongthediscussedtruncationprotocolsinTable4.CrypT-
|     |     |     |     |     |     |     | Flow2’s | faithful | truncation |     | involves | a   | single | call to F(cid:96)−1, |
| --- | --- | --- | --- | --- | --- | --- | ------- | -------- | ---------- | --- | -------- | --- | ------ | -------------------- |
Mill
|     |     |     |     |     |     |     | (cid:0)4(cid:1) | ,F2(cid:96) |     | f   |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --------------- | ----------- | --- | --- | --- | --- | --- | --- |
Proposition3 Givenanunsigned(cid:96)-bitintegerxanditsarith- -OT ,andF .Thisleadstoacommunicationup-
|     |     |     |     |     |     |     | 1   | (cid:96) B2A |     | Mill |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ------------ | --- | ---- | --- | --- | --- | --- |
meticsharesx andx ,definew=1{x +x >2(cid:96)−1}.Let perboundofλ((cid:96)+f+2)+19(cid:96)+14f bitswhensub-block
|     |     | 0 1 |     |     | 0 1 |     |     |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

ciphertext(b,a)∈ZN+1
Table4:Communicationcomplexityoftruncationprotocols ice needs to sendan LWE to Bob
q
of(cid:96)-bitintegerstruncatedby f bits. for decryption. Our optimization suggests Alice send just
|     |     |     |     |     | some of | the high-end | bits | of b and | the values | in  | a to Bob |
| --- | --- | --- | --- | --- | ------- | ------------ | ---- | -------- | ---------- | --- | -------- |
TruncationProtocol Communication(bits) and skip the remaining low-end parts. In brief, Alice can
|     |              |                                |                |     | skip the                | low (cid:96) = | (cid:98)log (q/p)(cid:99)−1              |     | bits | of b and | the low |
| --- | ------------ | ------------------------------ | -------------- | --- | ----------------------- | -------------- | ---------------------------------------- | --- | ---- | -------- | ------- |
|     | Faithful[46] | λ((cid:96)+f+2)+19(cid:96)+14f |                |     |                         | b              | √ 2                                      |     |      |          |         |
|     |              |                                |                |     | (cid:96) a =(cid:98)log | (q/(6.6        | Np))(cid:99)bitsofthevaluesinawhentrans- |     |      |          |         |
|     |              |                                | 16(cid:96)+11f |     |                         | 2              |                                          |     |      |          |         |
Faithful(VOLE) ferringtheciphertexttoBob.Bobmightfailtodecryptthe
“deform”ciphertextatanegligiblechance(i.e.,<2−38).In-
| One-bitapprox.(VOLE) |     |     | 13(cid:96) |     |     |     |     |     |     |     |     |
| -------------------- | --- | --- | ---------- | --- | --- | --- | --- | --- | --- | --- | --- |
deed,thisoptimizationsavesabout16%–25%ofthecommu-
| One-bitapprox.(VOLE,MSB) |     |     | f+4 |     |     |     |     |     |     |     |     |
| ------------------------ | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
nicationsentbyAliceinourHE-basedprotocols.Wedeferthe
|     |     |     |     |     | calculationof(cid:96) | b and(cid:96) | a tothefullversionofthismanuscript. |     |     |     |     |
| --- | --- | --- | --- | --- | --------------------- | ------------- | ----------------------------------- | --- | --- | --- | --- |
lengthm=4inthemillionaires’protocol.Adirectreplace-
mentofOTwiththeVOLEversiongivesusanupperbound
6 Evaluations
| of 16(cid:96)+11f | bits,according | to our complexity |                  | analysis in |     |     |     |     |     |     |     |
| ----------------- | -------------- | ----------------- | ---------------- | ----------- | --- | --- | --- | --- | --- | --- | --- |
|                   | 2 (cid:96)     |                   | (cid:0)2 (cid:1) |             |     |     |     |     |     |     |     |
Table 2 and 3 (F uses a single call of -COT (cid:96) ). One- 6.1 ExperimentSetup
|                                                  | B 2 A |     | 1   |          |     |     |     |     |     |     |     |
| ------------------------------------------------ | ----- | --- | --- | -------- | --- | --- | --- | --- | --- | --- | --- |
| bitapproximatetruncationinvolvesacalltoF(cid:96) |       |     |     | andF2f , |     |     |     |     |     |     |     |
B2A
|       |                       |               | Mill       |        | OurimplementationisbuiltontopoftheSEALlibrary[49] |     |     |     |     |     |     |
| ----- | --------------------- | ------------- | ---------- | ------ | ------------------------------------------------- | --- | --- | --- | --- | --- | --- |
| which | gives a communication | of 13(cid:96) | bits. When | MSB is |                                                   |     |     |     |     |     |     |
known,thecostisreducedto f+4bits. withtheHEXLacceleration[30]andtheEMPtoolkit[55].
|     |     |     |     |     | WealsoextendtheFerret2 |     |     | protocolinEMPtosupportvar- |     |     |     |
| --- | --- | --- | --- | --- | ---------------------- | --- | --- | -------------------------- | --- | --- | --- |
(cid:0)n(cid:1)
|                        |     |     |     |     | ious application-level |         | OT          | types, such | as  | -OT (cid:96) . | To com-  |
| ---------------------- | --- | --- | --- | --- | ---------------------- | ------- | ----------- | ----------- | --- | -------------- | -------- |
| 5 FurtherOptimizations |     |     |     |     |                        |         |             |             |     | 1              |          |
|                        |     |     |     |     | pare, we               | use the | open-source | library     | SCI | that           | provided |
HE
|     |     |     |     |     | by the authors | ofCrypTFlow2. |     | Besides |     | the OT-basednon- |     |
| --- | --- | --- | --- | --- | -------------- | ------------- | --- | ------- | --- | ---------------- | --- |
Wepresentsomeoptimizationsthathavenotbeenconsidered
|     |     |     |     |     | linearprotocolsinCrypTFlow2,SCI |     |     |     | HE alsooffersmanyop- |     |     |
| --- | --- | --- | --- | --- | ------------------------------- | --- | --- | --- | -------------------- | --- | --- |
inthepreviousinferencesystems[6,34,41,46].Someofour
timizedimplementationofstate-of-the-artsincludingthese-
optimizationscanalsobeappliedtothesesystems. cureconvolution[34,41],andthematrix–vectormultiplica-
tionfrom[12,25]usinganoldversionofSEAL.Forafair
5.1 ReducingComputationOverhead comparison,wemodifythecodeinSCI toadoptthelat-
HE
estversionofSEALandtoapplyHEXLacceleration.Both
TheBNlayercanbeplacedrightafteraCONVorFClayer.
|     |     |     |     |     | CheetahandSCI |     | areimplementedinC++andcompiled |     |     |     |     |
| --- | --- | --- | --- | --- | ------------- | --- | ------------------------------ | --- | --- | --- | --- |
HE
Forinstance,58 outofthe 121 BN layers in DenseNet121 bygcc(version8.4.0)onUbuntu18.04.
areplacedrightafteraCONVlayer.Weobservethatwecan
TestbedEnvironment.Allthefollowingexperimentswere
apply the BN fusion technique to save the computation of performedonAlibabaCloudwitha2.70GHzprocessorand
| HomBN | since the weights | ofthe BN | layerandthe | CONV |              |         |     |                   |     |     |          |
| ----- | ----------------- | -------- | ----------- | ---- | ------------ | ------- | --- | ----------------- | --- | --- | -------- |
|       |                   |          |             |      | 16 gigabytes | of RAM. | We  | ran ourbenchmarks |     | in  | two net- |
layerarealreadyknownbyAlice.Specifically,foreachBN-
|     |     |     |     |     | worksettings. | The | bandwidthbetween |     | the | cloudinstances |     |
| --- | --- | --- | --- | --- | ------------- | --- | ---------------- | --- | --- | -------------- | --- |
then-CONVstructureintheDNN,Alicefirstmultipliesthe wereabout384MBps(LAN)and44MBps(WAN),respec-
weightsoftheBNlayer(i.e.,µ)tothekernelKoftheCONV
tively.Theround-triptimewereabout0.3ms(LAN)and40ms
layer. Then Alice and Bob jointly invoke the HomCONV (WAN),respectively.
protocolonthescaledkernel.AfterHomCONV,Aliceadds
ConcreteSEAL’sParameters.Weinstantiateourprotocols
theshiftvectorθtoheradditiveshare.Interestingly,byusing
|     |     |     |     |     | usingtheSEALparametersHE.pp |     |     |     |     | ={N=4096,q≈ |     |
| --- | --- | --- | --- | --- | --------------------------- | --- | --- | --- | --- | ----------- | --- |
Cheetah
BNfusion,wealsosavethecomputationoftruncationsince 2105,p=237,σ=3.2}.Recallthatthecurrentsecureconvo-
wehavesavedonedepthoffixed-pointmultiplication.
|     |     |     |     |     | lutionprotocolinSCI |     | [48]demandsHW/s2≤N/2.For |     |     |     |     |
| --- | --- | --- | --- | --- | ------------------- | --- | ------------------------ | --- | --- | --- | --- |
HE
mostofthetime,itcanbeinstantiatedusingtheSEALpa-
={N=8192,q≈2180,p≈237,σ=3.2}.
| 5.2 | ReducingCommunicationOverhead |     |     |     | rametersHE.pp |     |     |     |     |     |     |
| --- | ----------------------------- | --- | --- | --- | ------------- | --- | --- | --- | --- | --- | --- |
SCI
Ontheotherhand,tohandletheconvolutiononlargetensors
We present two orthogonal optimizations for reducing the wehavetoinstantiateSCI
HE usingalargerlatticedimension
volumeofciphertextssentbyAliceinourprotocols.
e.g.,N=32768intheirimplementation.Thesecuritylevels
Intheproposedlinearprotocols,AlicesendsmanyLWE underthese parameters are notalignedbutallofthem can
ciphertextsbacktoBobfordecryption.Indeed,someofthe
provideatleastλ=128bitsofsecurityaccordingtoSEAL.
LWEciphertextswillsharethesamevectoraintheirsecond
DNNArchitectures.WemeasuretheperformanceofChee-
componentiftheyareextractedfromthesameRLWEcipher-
tahon6DNNs(Table9).Forinstance,theResNet50istrained
text.Toreducethecommunicationoverhead,Alicecanonly
toclassifyRGBimagesof224×224pixelsinto1001classes.
sendonecopyofthisvectortoBob. The ResNet50 has over23 million trainable parameters. It
| Our | second optimization | comes from | an insightful | ob- |     |     |     |     |     |     |     |
| --- | ------------------- | ---------- | ------------- | --- | --- | --- | --- | --- | --- | --- | --- |
servation to the (R)LWE decryption formula. Suppose Al- 2OurprotocolcanuseanyVOLE-styleOTextensionsuchas[9,14,56].

Table 5: Comparing the running time and communication Table 6: Comparing the running time and communication
costs of our linear protocols with the state-of-the-arts. All costsofournon-linearprotocolswiththestate-of-the-art.All
runswereexecutedusingsinglethread.1MB=220bytes. runswereexecutedusingsinglethread.Thecommunication
andtimingareaccumulatedfor216runsoftheprotocols.
End2EndTime
ni,no
| FC  |           |                 | Commu. |           |        |             |        |
| --- | --------- | --------------- | ------ | --------- | ------ | ----------- | ------ |
|     |           | LAN WAN         |        |           |        | End2EndTime |        |
|     |           |                 |        | Benchmark | Method |             | Commu. |
|     |           |                 |        |           |        | LAN WAN     |        |
|     | 2048,1001 | 1,533ms 1,587ms | 0.50MB |           |        |             |        |
[46,48]
|     | 512,10    | 17ms 60ms   | 0.50MB |             | [46] | 572ms 1,680ms | 31.56MB |
| --- | --------- | ----------- | ------ | ----------- | ---- | ------------- | ------- |
|     |           |             |        | Millionaire | Ours | 496ms 663ms   | 2.72MB  |
|     | 2048,1001 | 111ms 171ms | 1.83MB |             |      |               |         |
Ours
|     | 512,10 | 4ms 51ms | 0.11MB |     |      | 1.1× 2.5×     | 11.6×   |
| --- | ------ | -------- | ------ | --- | ---- | ------------- | ------- |
|     |        |          |        |     | [46] | 544ms 1,914ms | 34.57MB |
End2EndTime
| CONV | HW,C,M,h,s |         | Commu. | Truncation | Ours | 432ms 655ms | 2.86MB |
| ---- | ---------- | ------- | ------ | ---------- | ---- | ----------- | ------ |
|      |            | LAN WAN |        |            |      |             |        |
|      |            |         |        |            |      | 1.2× 2.9×   | 12.0×  |
2242,3,64,7,2
|         |                | 25.52s 27.28s | 76.02MB |            | [45,46] | 213ms 716ms | 14.09MB |
| ------- | -------------- | ------------- | ------- | ---------- | ------- | ----------- | ------- |
|         | 2242,3,64,3,2  | 7.06s 8.78s   | 76.02MB | Trunc.with |         |             |         |
| [46,48] |                |               |         |            | Ours    | 31ms 101ms  | 0.16MB  |
|         | 562,64,256,1,1 | 8.21s 8.74s   | 28.01MB | knownMSB   |         |             |         |
|         |                |               |         |            |         | 6.8× 7.1×   | 88.0×   |
|         | 562,256,64,1,1 | 7.41s 8.51s   | 52.02MB |            |         |             |         |
2242,3,64,7,2
|     |     | 1.30s 2.11s | 49.62MB |     |     |     |     |
| --- | --- | ----------- | ------- | --- | --- | --- | --- |
2242,3,64,3,2 1.33s 2.16s 49.62MB agethehomomorphicrotationcouldonlyacceptsharesfrom
Ours
562,64,256,1,1 0.83s 1.10s 15.30MB a prime filed Z . To accept shares from Z ,they need to
|     |                |             |         |     | p   | 2(cid:96) |     |
| --- | -------------- | ----------- | ------- | --- | --- | --------- | --- |
|     | 562,256,64,1,1 | 0.70s 0.99s | 17.07MB |     |     |           |     |
applytheChineseRemainderTheoremtoexpandtheplain-
|     |     |     |     | text modulus | to above (2(cid:96)+1+40) | bits for | achieving 40- |
| --- | --- | --- | --- | ------------ | ------------------------- | -------- | ------------- |
End2EndTime
BN HW,C Commu. bit statistical security [18]. The downside is that it will in-
|     |     | LAN WAN |     |     |     |     |     |
| --- | --- | ------- | --- | --- | --- | --- | --- |
creasethecomputationandcommunicationcostsbyafactor
562,64
0.28s 0.50s 12.51MB ofO((2(cid:96)+1+40)/(cid:96))whichisabout4forourparameters.
[46,48]
|      | 562,256 | 1.14s 2.17s | 49.01MB |                           |     |     |     |
| ---- | ------- | ----------- | ------- | ------------------------- | --- | --- | --- |
|      | 562,64  | 0.22s 0.34s | 6.84MB  |                           |     |     |     |
| Ours |         |             |         | 6.2.2 Non-linearFunctions |     |     |     |
|      | 562,256 | 0.88s 1.36s | 27.34MB |                           |     |     |     |
Wealsobenchmarkthenon-linearfunctionsinTable6,by
|     |     |     |     | running SCI | andCheetahwitha | single threadunderthe |     |
| --- | --- | --- | --- | ----------- | --------------- | --------------------- | --- |
HE
LANandWANsettings.Theperformanceaccountsfor216
consistsof53CONVlayers,49BNlayersand1FClayer.For
thenon-linearoperations,ResNet50consistsof49ReLU,98 callstotheprotocols,whichresemblesascenarioofbatch
truncation,1max-pooling,1average-poolingand1argmax. execution in neural network inference. From the table,we
Metrics.Wemeasurethetotalcommunicationincludingall observethatoursolutionsignificantlyreducesthecommuni-
themessagessentbyAliceandBobbutexcludingtheone- cationcost,i.e.,bymorethan10×inallnon-linearprotocols.
TheimprovementscomefromboththeVOLE-styleOTup-
timesetup(e.g.,keysgenerationandbase-OT).Wemeasure
theend-to-endrunningtimeincludingthetimeoftransferring grades,andourmoreconciseprotocoldesigns.
messagesthroughtheLAN/WANbutweruleoutthetimefor
| HEkeygenerationandbase-OT. |     |     |     | 6.3 ComparisonwithDELPHI |     |     |     |
| -------------------------- | --- | --- | --- | ------------------------ | --- | --- | --- |
InTable7,wecompareCheetahwithDELPHI[41],oneof
6.2 Microbenchmarks
|     |     |     |     | the state-of-the-art | 2PC-NN | systems. Similar | to DELPHI, |
| --- | --- | --- | --- | -------------------- | ------ | ---------------- | ---------- |
6.2.1 LinearFunctions weperformthesecomputationsontheCIFARdataset[36]
withalargerbit-widthof(cid:96)=41intheWANsettingusing
Wecomparetheperformanceoftheproposedlinearprotocols
4threads.NotethatCheetah’sHE-basedprotocolsarealso
| withthecounterpartsimplementedinSCI |                    | inTable5.The |             |                                                       |     |     |     |
| ----------------------------------- | ------------------ | ------------ | ----------- | ----------------------------------------------------- | --- | --- | --- |
|                                     |                    | HE           |             | compatiblewiththeonline/offlineoptimizations[4]usedby |     |     |     |
| keytakeawayis                       | thatourcomputation | time is      | about1.3× – |                                                       |     |     |     |
DELPHI.Thus,inTable7,wepresentthesumoftheoffline
| 20×fasterthanSCI | ’s,andourcommunicationcostisabout |     |     |                                                    |     |     |     |
| ---------------- | --------------------------------- | --- | --- | -------------------------------------------------- | --- | --- | --- |
|                  | HE                                |     |     | andonlinecostsofDELPHIreportedintheirpaper(updated |     |     |     |
1.5×–2×lower3,dependingontheinputsize.
version).Here,Cheetahisabout1orderofmagnitudefaster
Moreover,ourlinearprotocolscanacceptadditiveshares
thanDELPHIandabout2ordersofmagnitudeefficientthan
| fromtheringZ | thatismorefriendlyforsubsequentnon- |     |     |                                                |     |     |     |
| ------------ | ----------------------------------- | --- | --- | ---------------------------------------------- | --- | --- | --- |
|              | 2(cid:96)                           |     |     | DELPHIintermsofcommunication.Cheetahcangivethe |     |     |     |
linearlayers,whilepriorapproaches[25,34,41,46]thatlever-
sameoutputasDELPHIsincebothframeworkswillintroduce
1-biterrorineachtruncationifweassumetheharshtruncation
3TheonlyexceptionistheFClayer,whereourcommunicationcostmay
errorinDELPHIdoesnotoccuronshallowNNs.
be1.33MBhigherthantheirs.

|                                                  |     |     |     |     |     |     | Table8:PerformancecomparisonwithSCI |     |     |     |     | andSecureQ8 |     |
| ------------------------------------------------ | --- | --- | --- | --- | --- | --- | ----------------------------------- | --- | --- | --- | --- | ----------- | --- |
| Table7:PerformancecomparisonwithDELPHI[41,Figure |     |     |     |     |     |     |                                     |     |     |     | HE  |             |     |
13]intheLANsetting.InputstothebenchmarkswereRGB (three-party)onlarge-scaleDNNs.Weusedtheprecision f =
imagesof32×32pixels.Alignedparametersofsharingmod- 12forfixed-pointvaluesand4threadsforthebenchmarks.
ulotoZ
| 241                                | andfixed-pointprecisionto |            |     |             | f =11withDELPHI |        |           |              |         |             |        |        |     |
| ---------------------------------- | ------------------------- | ---------- | --- | ----------- | --------------- | ------ | --------- | ------------ | ------- | ----------- | ------ | ------ | --- |
| wereusedforCheetahinthisbenchmark. |                           |            |     |             |                 |        |           |              |         | End2EndTime |        |        |     |
|                                    |                           |            |     |             |                 |        | Benchmark |              | System  |             |        | Commu. |     |
|                                    |                           |            |     |             |                 |        |           |              |         | LAN         | WAN    |        |     |
| Benchmark                          |                           | System     |     | End2EndTime |                 | Commu. |           |              |         |             |        |        |     |
|                                    |                           |            |     |             |                 |        |           | SCI          | HE [46] | 41.1s       | 147.2s | 5.9GB  |     |
|                                    |                           | DELPHI[41] |     |             | ≈110s           | ≈3.6GB | SqNet     | SecureQ8[15] |         | 4.4s        | 134.1s | 0.8GB  |     |
|                                    |                           |            |     |             |                 |        |           |              | Cheetah | 16.0s       | 39.1s  | 0.5GB  |     |
| MiniONN                            |                           | Cheetah    |     |             | 3.55s           | 0.03GB |           |              |         |             |        |        |     |
|                                    |                           |            |     |             | ≈30×            | ≈117×  |           | SCI          | [46]    | 295.7s      | 759.1s | 29.2GB |     |
HE
|          |     | DELPHI[41] |     |     | ≈200s  | ≈6.5GB | RN50 | SecureQ8[15] |         | 32.6s  | 379.2s | 3.8GB  |     |
| -------- | --- | ---------- | --- | --- | ------ | ------ | ---- | ------------ | ------- | ------ | ------ | ------ | --- |
| ResNet32 |     | Cheetah    |     |     | 15.95s | 0.11GB |      |              | Cheetah | 80.3s  | 134.7s | 2.3GB  |     |
|          |     |            |     |     | ≈12×   | ≈58×   |      |              |         |        |        |        |     |
|          |     |            |     |     |        |        |      | SCI          | [46]    | 296.2s | 929.0s | 35.4GB |     |
HE
| 1GB=230bytes. |     |     |     |      |     |     | DNet                                            | SecureQ8[15] |         | 22.5s | 342.6s | 4.6GB |     |
| ------------- | --- | --- | --- | ---- | --- | --- | ----------------------------------------------- | ------------ | ------- | ----- | ------ | ----- | --- |
|               |     |     |     |      |     |     |                                                 |              | Cheetah | 79.3s | 177.7s | 2.4GB |     |
| ×101          |     |     |     | ×101 |     |     | SqNet=SqueezeNet;RN50=ResNet50;DNet=DenseNet121 |              |         |       |        |       |     |
1.50
|      |     | SCI-HE  |     | 2.6 |     | SCI-HE  |     |     |     |     |     |     |     |
| ---- | --- | ------- | --- | --- | --- | ------- | --- | --- | --- | --- | --- | --- | --- |
| 1.48 |     |         |     | 2.4 |     |         |     |     |     |     |     |     |     |
|      |     | Cheetah |     |     |     | Cheetah |     |     |     |     |     |     |     |
| 1.46 |     |         |     | 2.2 |     |         |     |     |     |     |     |     |     |
1.44
usinganimagesetthatincludesabout1,000imagesfromIm-
| 1.42 |     |     |     | 2.0 |     |     |                                                     |     |     |     |     |     |     |
| ---- | --- | --- | --- | --- | --- | --- | --------------------------------------------------- | --- | --- | --- | --- | --- | --- |
| 1.40 |     |     |     |     |     |     | ageNet.Foralltheseimages,Cheetahoutputsthesameclas- |     |     |     |     |     |     |
1.8
1.38
|      |       |       |     |     |       |             | sificationlabelasSCI                        |     |     | .Let’szoominabit.InFigure10, |     |               |        |
| ---- | ----- | ----- | --- | --- | ----- | ----------- | ------------------------------------------- | --- | --- | ---------------------------- | --- | ------------- | ------ |
| 1.36 |       |       |     | 1.6 |       |             |                                             |     | HE  |                              |     |               |        |
| 1.34 |       |       |     |     |       |             | wepresentthetop-10valuesin                  |     |     | theprediction                |     | vectors(i.e., |        |
| 0 1  | 2 3 4 | 5 6 7 | 8 9 | 0   | 1 2 3 | 4 5 6 7 8 9 |                                             |     |     |                              |     |               |        |
|      |       |       |     |     |       |             | theinputtothefinalArgMaxlayer)computedbySCI |     |     |                              |     |               | HE and |
Figure10:Thetop-10valuesinthepredictionvectorof1001 CheetahonResNet50andSqueezeNet.Herewecanseethat
CheetahgivesalmostthesamepredictionvectorsasSCI
| valuesfromSqueezeNet(left)andResNet50(right). |     |     |     |     |     |     |     |     |     |     |     |     | HE  |
| --------------------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
whicharebit-wiseequivalenttotheplaintextfixed-pointcom-
|     |     |     |     |     |     |     | putation. Also, | according |     | to the extensive | experiments |     | in  |
| --- | --- | --- | --- | --- | --- | --- | --------------- | --------- | --- | ---------------- | ----------- | --- | --- |
6.4 ComparisonwithCrypTFlow2
CrypTFlow2[46,Table10],thepredictionaccuracyachieved
|     |     |     |     |     |     |     | by fixed-point | computation |     | can match | the accuracy |     | of the |
| --- | --- | --- | --- | --- | --- | --- | -------------- | ----------- | --- | --------- | ------------ | --- | ------ |
Withallourprotocolsandoptimizationsinplace,wedemon- floating-pointcounterpart.Weconcludethatourapproximate
stratetheperformanceofCheetahbyrunningcryptographic
truncationprotocolsareeffectiveforthe2PC-NNsetting.
| inferences                                        | on large  | DNNs     | efficiently. |            | Table      | 8 shows that |            |     |     |     |     |     |     |
| ------------------------------------------------- | --------- | -------- | ------------ | ---------- | ---------- | ------------ | ---------- | --- | --- | --- | --- | --- | --- |
| Cheetah is                                        | efficient | enough   | to           | evaluate   | SqueezeNet | [29],        |            |     |     |     |     |     |     |
| ResNet50[26],andDenseNet121[28]within3minuteseven |           |          |              |            |            |              | Conclusion |     |     |     |     |     |     |
| under the                                         | WAN       | setting. | The          | end-to-end | running    | time of      |            |     |     |     |     |     |     |
Cheetah was about 2× – 5× faster than SCI within 8% Secure two-party deep neural network inference is getting
HE
| bandwidthconsumptionofSCI |     |     |     | .Tothebestofourknowl- |     |     |     |     |     |     |     |     |     |
| ------------------------- | --- | --- | --- | --------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
HE closerto practicality. Cheetah presents a highly optimized
edge,nopriorsecuretwo-partyinferencesystemcanevaluate architecturethatrunsthecomplexResNet50modelinless
ResNet50 and DenseNet121 within 10 minutes under the than 2.5 minutes even under the WAN setting,consuming
commodityhardwareandnetworkconditionsasours. 2.3GBofcommunication.Theevidentialimprovementover
Compare with a Three-party Approach. In Table 8, we stage-of-the-artcomesfromasetofnovelcryptographicpro-
also provide the performance ofSecureQ8 [15],one ofthe tocolsthatarebuiltuponamoreprofoundexplorationofthe
mostefficientthree-partysecureinferenceframework.These problem-setting.Cheetahalsoprovidebetteralternativesto
resultsareobtainedbyre-runningtheirimplementation[50] awidespectrumoffunctionalevaluationproblemsinsecure
underoursenvironment.Asisshown,SecureQ8was3×-4× two-partycomputation. Oneofourfurtureworkistoapply
faster than Cheetah on LAN,while Cheetah was 2× - 3× orthogonaloptimizationscommonlyadoptedinDNNsuchas
fasteronWANbythevirtueoflesscommunication4.
quantizationandhardwareacceleration.Webelievetheday
|     |     |     |     |     |     |     | is not that | faroff | when | some applications | such | as privacy- |     |
| --- | --- | --- | --- | --- | --- | --- | ----------- | ------ | ---- | ----------------- | ---- | ----------- | --- |
preservingmedicaldiagnosiscouldbedoneinseconds.
6.5 EffectiveApproximateTruncation
|     |     |     |     |     |     |     | Acknowledgment. |     | The | authors would | like | to thank | the |
| --- | --- | --- | --- | --- | --- | --- | --------------- | --- | --- | ------------- | ---- | -------- | --- |
anonymousreviewersfortheirinsightfulcommentsandDr.
Todemonstratetheeffectivenessofourapproximatetrunca-
tionprotocols,weperformedmorepredictionsonSqueezeNet MarinaBlantonfortheshepherding.Theauthorswouldalso
liketothankChenKaiWengfromNorthwesternUniversity
4Notethattheimplementation[50]usesfixedringsizesi.e.,(cid:96)∈{64,128}. forhelpfuldiscussionsonFerret.

References [13] Hao Chen, Wei Dai, Miran Kim, and Yongsoo Song.
Efficienthomomorphicconversionbetween(ring)LWE
[1] MartínAbadi,AndyChu,IanJ.Goodfellow,H.Brendan
|     |     |     |     |     |     | ciphertexts. | InKazueSakoandNilsOleTippenhauer, |     |     |     |     |
| --- | --- | --- | --- | --- | --- | ------------ | --------------------------------- | --- | --- | --- | --- |
McMahan,IlyaMironov,KunalTalwar,andLiZhang. editors,ACNS,volume12726,pages460–479,2021.
| Deeplearningwithdifferentialprivacy. |     |     |     | InCCS,pages |     |     |     |     |     |     |     |
| ------------------------------------ | --- | --- | --- | ----------- | --- | --- | --- | --- | --- | --- | --- |
308–318,2016. [14] GeoffroyCouteau,PeterRindal,andSrinivasanRaghu-
|     |     |     |     |     |     | raman. | Silver: | Silent VOLE | and oblivious |     | transfer |
| --- | --- | --- | --- | --- | --- | ------ | ------- | ----------- | ------------- | --- | -------- |
[2] NitinAgrawal,AliShahinShamsabadi,MattJ.Kusner,
|     |     |     |     |     |     | fromhardnessofdecodingstructuredLDPCcodes. |     |     |     |     | In  |
| --- | --- | --- | --- | --- | --- | ------------------------------------------ | --- | --- | --- | --- | --- |
andAdriàGascón.QUOTIENT:two-partysecureneural CRYPTO,pages502–534,2021.
| networktrainingandprediction. |     |     | InCCS,pages1231– |     |     |     |     |     |     |     |     |
| ----------------------------- | --- | --- | ---------------- | --- | --- | --- | --- | --- | --- | --- | --- |
1247,2019. [15] Anders P. K. Dalskov, Daniel Escudero, and Marcel
|     |     |     |     |     |     | Keller. Secureevaluationofquantizedneuralnetworks. |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | -------------------------------------------------- | --- | --- | --- | --- | --- |
[3] GiladAsharov,YehudaLindell,ThomasSchneider,and
Proc.Priv.EnhancingTechnol.,2020(4):355–375,2020.
| MichaelZohner. |     | MoreEfficientObliviousTransferand |     |     |     |     |     |     |     |     |     |
| -------------- | --- | --------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
ExtensionsforFasterSecureComputation. InProceed- [16] Anders P. K. Dalskov, Daniel Escudero, and Marcel
ings of the 2013 ACM SIGSAC Conference on Com- Keller.Fantasticfour:Honest-majorityfour-partysecure
puter and Communications Security, pages 535–548, computationwithmalicioussecurity. InMichaelBailey
NewYork,NY,USA,2013. andRachelGreenstadt,editors,USENIX,pages2183–
2200,2021.
| [4] Donald Beaver. |     | Efficient | multiparty | protocols | using |     |     |     |     |     |     |
| ------------------ | --- | --------- | ---------- | --------- | ----- | --- | --- | --- | --- | --- | --- |
circuitrandomization. InCRYPTO,volume576,pages [17] RoshanDathathri,OlliSaarikivi,HaoChen,KimLaine,
| 420–432,1991. |     |     |     |     |     | KristinE.Lauter,SaeedMaleki,MadanlalMusuvathi, |     |                           |     |     |     |
| ------------- | --- | --- | --- | --- | --- | ---------------------------------------------- | --- | ------------------------- | --- | --- | --- |
|               |     |     |     |     |     | andToddMytkowicz.                              |     | CHET:anoptimizingcompiler |     |     |     |
[5] MichaelBen-Or,ShafiGoldwasser,andAviWigderson.
|              |          |     |                       |     |        | forfully-homomorphicneural-networkinferencing. |     |     |     |     | In  |
| ------------ | -------- | --- | --------------------- | --- | ------ | ---------------------------------------------- | --- | --- | --- | --- | --- |
| Completeness | theorems |     | for non-cryptographic |     | fault- |                                                |     |     |     |     |     |
SIGPLAN,pages142–156,2019.
| tolerantdistributedcomputation(extendedabstract). |     |     |     |     | In  |     |     |     |     |     |     |
| ------------------------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
STOC,pages1–10.ACM,1988. [18] Daniel Demmler, Thomas Schneider, and Michael
|                              |     |          |                   |         |      | Zohner.                             | ABY | - A framework | for | efficient  | mixed- |
| ---------------------------- | --- | -------- | ----------------- | ------- | ---- | ----------------------------------- | --- | ------------- | --- | ---------- | ------ |
| [6] Fabian Boemer,           |     | Anamaria | Costache,         | Rosario | Cam- |                                     |     |               |     |            |        |
|                              |     |          |                   |         |      | protocolsecuretwo-partycomputation. |     |               |     | InNDSS.The |        |
| marota,andCasimirWierzynski. |     |          | nGraph-HE2:Ahigh- |         |      |                                     |     |               |     |            |        |
InternetSociety,2015.
throughputframeworkforneuralnetworkinferenceon
encrypteddata. InWAHC,pages45–56.ACM,2019. [19] DanielEscudero,SatrajitGhosh,MarcelKeller,Rahul
|     |     |     |     |     |     | Rachuri, | and Peter | Scholl. | Improved | primitives | for |
| --- | --- | --- | --- | --- | --- | -------- | --------- | ------- | -------- | ---------- | --- |
[7] FabianBoemer,YixingLao,RosarioCammarota,and
MPCovermixedarithmetic-binarycircuits.InCRYPTO,
| CasimirWierzynski. |     | nGraph-HE:agraphcompilerfor |     |     |     |     |     |     |     |     |     |
| ------------------ | --- | --------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
pages823–852,2020.
| deeplearningonhomomorphicallyencrypteddata. |     |     |     |     | In  |     |     |     |     |     |     |
| ------------------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
ComputingFrontiers,pages3–13,2019. [20] CraigGentry,ShaiHalevi,andNigelP.Smart. Homo-
|     |     |     |     |     |     | morphic | evaluation | of the | AES circuit. | In CRYPTO, |     |
| --- | --- | --- | --- | --- | --- | ------- | ---------- | ------ | ------------ | ---------- | --- |
[8] RaphaelBost,RalucaAdaPopa,StephenTu,andShafi
pages850–867,2012.
| Goldwasser.  | Machine      | learning | classification |     | overen- |                          |     |        |         |     |        |
| ------------ | ------------ | -------- | -------------- | --- | ------- | ------------------------ | --- | ------ | ------- | --- | ------ |
| crypteddata. | InNDSS,2015. |          |                |     |         |                          |     |        |         |     |        |
|              |              |          |                |     |         | [21] Ran Gilad-Bachrach, |     | Nathan | Dowlin, | Kim | Laine, |
[9] EletteBoyle,GeoffroyCouteau,NivGilboa,YuvalIshai, Kristin E. Lauter,Michael Naehrig,and John Werns-
ing.CryptoNets:Applyingneuralnetworkstoencrypted
| LisaKohl,PeterRindal,andPeterScholl. |                          |     |                        |     | Efficienttwo- |                                    |     |     |     |              |     |
| ------------------------------------ | ------------------------ | --- | ---------------------- | --- | ------------- | ---------------------------------- | --- | --- | --- | ------------ | --- |
|                                      |                          |     |                        |     |               | datawithhighthroughputandaccuracy. |     |     |     | InICML,pages |     |
| round OT                             | extension                | and | silent non-interactive |     | secure        |                                    |     |     |     |              |     |
| computation.                         | InCCS,pages291–308,2019. |     |                        |     |               | 201–210,2016.                      |     |     |     |              |     |
[10] AlonBrutzkus,RanGilad-Bachrach,andOrenElisha. [22] Oded Goldreich. The Foundations of Cryptography -
Low latency privacy preserving inference. In ICML, Volume2: BasicApplications. CambridgeUniversity
Press,2004.
pages812–821,2019.
[23] ThoreGraepel,KristinE.Lauter,andMichaelNaehrig.
| [11] Ran Canetti. |     | Security | and composition |     | of multi- |     |     |     |     |     |     |
| ----------------- | --- | -------- | --------------- | --- | --------- | --- | --- | --- | --- | --- | --- |
partycryptographicprotocols. JournalofCryptology, MLConfidential:Machinelearningonencrypteddata.
13(1):143–202,2000. InTaekyoungKwon,Mun-KyuLee,andDaesungKwon,
editors,ICISC,pages1–21,2012.
| [12] HaoChen,WeiDai,MiranKim,andYongsooSong. |     |     |     |     | Ef- |     |     |     |     |     |     |
| -------------------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
ficientmulti-keyhomomorphicencryptionwithpacked [24] V. Gulshan, L. Peng, M. Coram, M. C. Stumpe,
ciphertextswithapplicationtoobliviousneuralnetwork D.Wu,A.Narayanaswamy,S.Venugopalan,K.Wid-
inference. InCCS,pages395–412,2019. ner,T. Madams,J. Cuadros,R. Kim,R. Raman,P. C.

Nelson,J.L.Mega,,andD.R.Webster. Development [38] YehudaLindell. Howtosimulateit-Atutorialonthe
andvalidationofadeeplearningalgorithmfordetection simulationprooftechnique. InYehudaLindell,editor,
of diabetic retinopathy in retinal fundus photographs. Tutorials on the Foundations of Cryptography,pages
| JAMA,316:2402–2410,2016. |     |     |     |     | 277–346.2017. |     |     |     |     |
| ------------------------ | --- | --- | --- | --- | ------------- | --- | --- | --- | --- |
[25] ShaiHaleviandVictorShoup. AlgorithmsinHElib. In [39] JianLiu,MikaJuuti,YaoLu,andN.Asokan. Oblivious
CRYPTO,pages554–571,2014.
neuralnetworkpredictionsviaminionntransformations.
InCCS,pages619–631,2017.
[26] KaimingHe,XiangyuZhang,ShaoqingRen,andJian
Sun. Deepresiduallearningforimagerecognition. In [40] Wenjie Lu and Jun Sakuma. More practical privacy-
CVPR,pages770–778,2016.
preservingmachinelearningasAserviceviaefficient
|     |     |     |     |     | securematrixmultiplication. |     |     | InMichaelBrennerand |     |
| --- | --- | --- | --- | --- | --------------------------- | --- | --- | ------------------- | --- |
[27] EhsanHesamifard,HassanTakabi,MehdiGhasemi,and
KurtRohloff,editors,WAHC,pages25–36,2018.
| RebeccaN.Wright. |     | Privacy-preservingmachinelearn- |     |     |     |     |     |     |     |
| ---------------- | --- | ------------------------------- | --- | --- | --- | --- | --- | --- | --- |
| ingasaservice.   |     | PoPETs,2018(3):123–142,2018.    |     |     |     |     |     |     |     |
[41] PratyushMishra,RyanLehmkuhl,AkshayaramSrini-
|     |     |     |     |     | vasan,WentingZheng,andRalucaAdaPopa. |     |     |     | DELPHI: |
| --- | --- | --- | --- | --- | ------------------------------------ | --- | --- | --- | ------- |
[28] GaoHuang,ZhuangLiu,LaurensvanderMaaten,and
KilianQ.Weinberger. Denselyconnectedconvolutional Acryptographicinferenceserviceforneuralnetworks.
networks. InCVPR,pages2261–2269,2017. InUSENIX,pages2505–2522,2020.
[29] Forrest N. Iandola, Matthew W. Moskewicz, Khalid [42] PaymanMohasselandPeterRindal. ABY3:AMixed
Ashraf,SongHan,WilliamJ.Dally,andKurtKeutzer. Protocol Framework for Machine Learning. In CCS,
Squeezenet:Alexnet-levelaccuracywith50xfewerpa- pages35–52,2018.
| rametersand<1mbmodelsize. |     |     | CoRR,2016. |     |                                    |     |     |           |     |
| ------------------------- | --- | --- | ---------- | --- | ---------------------------------- | --- | --- | --------- | --- |
|                           |     |     |            |     | [43] PaymanMohasselandYupengZhang. |     |     | SecureML: | A   |
[30] IntelHEXL(release1.1.1).https://arxiv.org/abs/
systemforscalableprivacy-preservingmachinelearning.
| 2103.16400,March2021. |     |     |     |     | InSP,pages19–38.IEEE,2017. |     |     |     |     |
| --------------------- | --- | --- | --- | --- | -------------------------- | --- | --- | --- | --- |
[31] YuvalIshai,JoeKilian,KobbiNissim,andErezPetrank. [44] MoniNaorandBennyPinkas. ObliviousTransferand
| ExtendingObliviousTransfersEfficiently. |     |     |     | InCRYPTO, |                       |     |                           |     |     |
| --------------------------------------- | --- | --- | --- | --------- | --------------------- | --- | ------------------------- | --- | --- |
|                                         |     |     |     |           | PolynomialEvaluation. |     | InSTOC,pages245–254,1999. |     |     |
pages145–161,2003.
[45] DeevashwerRathee,MayankRathee,RahulKrantiKi-
[32] BargavJayaramanandDavidEvans. Evaluatingdiffer- ranGoli,DivyaGupta,RahulSharma,NishanthChan-
| entiallyprivatemachinelearninginpractice. |     |     |     | InNadia |               |     |                 |               |     |
| ----------------------------------------- | --- | --- | --- | ------- | ------------- | --- | --------------- | ------------- | --- |
|                                           |     |     |     |         | dran,andAseem |     | Rastogi. SiRnn: | A mathlibrary | for |
HeningerandPatrickTraynor,editors,USENIX,pages
|                 |     |     |     |     | secureRNNinference. |     | InSP,pages1003–1020.IEEE, |     |     |
| --------------- | --- | --- | --- | --- | ------------------- | --- | ------------------------- | --- | --- |
| 1895–1912,2019. |     |     |     |     | 2021.               |     |                           |     |     |
[33] XiaoqianJiang,MiranKim,KristinE.Lauter,andYong-
[46] DeevashwerRathee,MayankRathee,NishantKumar,
| sooSong. | Secureoutsourcedmatrixcomputationand |     |     |     |     |     |     |     |     |
| -------- | ------------------------------------ | --- | --- | --- | --- | --- | --- | --- | --- |
NishanthChandran,DivyaGupta,AseemRastogi,and
| application | to  | neuralnetworks. | In CCS,pages | 1209– |              |     |                                   |     |     |
| ----------- | --- | --------------- | ------------ | ----- | ------------ | --- | --------------------------------- | --- | --- |
|             |     |                 |              |       | RahulSharma. |     | CrypTFlow2:Practical2-partysecure |     |     |
1222,2018.
|     |     |     |     |     | inference. | InCCS,pages325–342.ACM,2020. |     |     |     |
| --- | --- | --- | --- | --- | ---------- | ---------------------------- | --- | --- | --- |
[34] ChiraagJuvekar,VinodVaikuntanathan,andAnantha
|               |     |                              |     |     | [47] M. | Sadegh Riazi, | Mohammad | Samragh, Hao | Chen, |
| ------------- | --- | ---------------------------- | --- | --- | ------- | ------------- | -------- | ------------ | ----- |
| Chandrakasan. |     | GAZELLE:Alowlatencyframework |     |     |         |               |          |              |       |
InUSENIX,pages KimLaine,KristinE.Lauter,andFarinazKoushanfar.
forsecureneuralnetworkinference.
XONN:XNOR-basedobliviousdeepneuralnetworkin-
1651–1669,2018.
|     |     |     |     |     | ference. | InNadiaHeningerandPatrickTraynor,editors, |     |     |     |
| --- | --- | --- | --- | --- | -------- | ----------------------------------------- | --- | --- | --- |
[35] VladimirKolesnikovandRanjitKumaresan. Improved USENIX,pages1501–1518,2019.
| OTextensionfortransferringshortsecrets. |     |     |     | InCRYPTO, |             |             |           |                |        |
| --------------------------------------- | --- | --- | --- | --------- | ----------- | ----------- | --------- | -------------- | ------ |
|                                         |     |     |     |           | [48] Secure | and correct | inference | (SCI) library. | https: |
pages54–70,2013.
//github.com/mpc-msri/EzPC/tree/master/SCI,
| [36] AlexKrizhevsky. |              | Learningmultiplelayersoffeatures |     |     | June2021. |     |     |     |     |
| -------------------- | ------------ | -------------------------------- | --- | --- | --------- | --- | --- | --- | --- |
| from                 | tiny images. | https://www.cs.toronto.edu/      |     |     |           |     |     |     |     |
~kriz/learning-features-2009-TR.pdf,2009. [49] MicrosoftSEAL(release3.6). https://github.com/
|              |              |                 |     |           | Microsoft/SEAL, |     | November | 2020. Microsoft | Re- |
| ------------ | ------------ | --------------- | --- | --------- | --------------- | --- | -------- | --------------- | --- |
| [37] Nishant | Kumar,Mayank | Rathee,Nishanth |     | Chandran, |                 |     |          |                 |     |
search,Redmond,WA.
DivyaGupta,AseemRastogi,andRahulSharma.CrypT-
Flow:Securetensorflowinference. InSP,pages336– [50] Multi-protocol SPDZ. https://github.com/
| 353.IEEE,2020. |     |     |     |     | data61/MP-SPDZ/tree/master,February2022. |     |     |     |     |
| -------------- | --- | --- | --- | --- | ---------------------------------------- | --- | --- | --- | --- |

[51] RezaShokri,MarcoStronati,CongzhengSong,andVi- • Correctness.OneverysetofmodelparametersW that
talyShmatikov. Membershipinferenceattacksagainst theserverholdsandeveryinputvectorxoftheclient,
machinelearningmodels. InSP,pages3–18,2017. theoutputoftheclientattheendoftheprotocolisthe
correctpredictionW(x).
| [52] Nigel | P. Smart | and | Frederik | Vercauteren. | Fully ho- |     |     |     |     |     |     |     |
| ---------- | -------- | --- | -------- | ------------ | --------- | --- | --- | --- | --- | --- | --- | --- |
momorphicSIMD operations. Des. Codes Cryptogr., • Privacy.Werequirethatacorrupted,semi-honestclient
71(1):57–81,2014. does not learn anything about the server’s network
|              |           |     |            |         |              | parameters |           | W. Formally, |     | we require | the  | existence |
| ------------ | --------- | --- | ---------- | ------- | ------------ | ---------- | --------- | ------------ | --- | ---------- | ---- | --------- |
| [53] Florian | Tramèrand |     | Dan Boneh. | Slalom: | Fast,verifi- |            |           |              |     |            |      | ViewΠ     |
|              |           |     |            |         |              | of an      | efficient | simulator    | Sim | such       | that | ≈         |
|              |           |     |            |         |              |            |           |              |     | C          |      | C c       |
ableandprivateexecutionofneuralnetworksintrusted Sim (meta,out)whereViewΠistheviewoftheclientin
|           |              |     |     |     |     | C   |     |     |     | C   |     |     |
| --------- | ------------ | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hardware. | InICLR,2019. |     |     |     |     |     |     |     |     |     |     |     |
theexecutionofΠ,metaincludesthemetainformation
(i.e.,thepublicparametersHE.pp,thepublickeypk,the
[54] FlorianTramèr,FanZhang,AriJuels,MichaelK.Re- numberoflayers,thesizeandtypeofeachlayer,andthe
| iter,andThomasRistenpart. |     |     |     | Stealingmachinelearning |     |     |     |     |     |     |     |     |
| ------------------------- | --- | --- | --- | ----------------------- | --- | --- | --- | --- | --- | --- | --- | --- |
activation)andoutdenotestheoutputoftheinference.
| modelsviapredictionapis. |     |     |     | InUSENIX,pages601–618, |     |         |         |      |              |             |     |        |
| ------------------------ | --- | --- | --- | ---------------------- | --- | ------- | ------- | ---- | ------------ | ----------- | --- | ------ |
|                          |     |     |     |                        |     | We also | require | that | a corrupted, | semi-honest |     | server |
2016.
doesnotlearnanythingabouttheprivateinputxofthe
client.Formally,werequiretheexistenceofanefficient
| [55] Xiao                                          | Wang,Alex | J.  | Malozemoff,and |     | Jonathan Katz. |              |     |               |     |       |             |     |
| -------------------------------------------------- | --------- | --- | -------------- | --- | -------------- | ------------ | --- | ------------- | --- | ----- | ----------- | --- |
|                                                    |           |     |                |     |                | simulatorSim |     | suchthatViewΠ |     | ≈ Sim | (meta)where |     |
| EMP-toolkit:EfficientMultiPartycomputationtoolkit. |           |     |                |     |                |              |     | S             |     | S c   | S           |     |
https://github.com/emp-toolkit,2016. ViewΠ istheviewoftheserverintheexecutionofΠ.
S
[56] KangYang,ChenkaiWeng,XiaoLan,JiangZhang,and
B SIMDandHomomorphicRotation
| Xiao                                                | Wang. | Ferret: | Fast extension |                       | for correlated OT |                                                   |     |                        |     |         |                |          |
| --------------------------------------------------- | ----- | ------- | -------------- | --------------------- | ----------------- | ------------------------------------------------- | --- | ---------------------- | --- | ------- | -------------- | -------- |
| withsmallcommunication.                             |       |         |                | InCCS,pages1607–1626, |                   |                                                   |     |                        |     |         |                |          |
| 2020.                                               |       |         |                |                       |                   | TheSIMDtechnique[52]usesadiscretefouriertransform |     |                        |     |         |                |          |
|                                                     |       |         |                |                       |                   | overtheprimefieldZ                                |     | toconvertvectorsv,u∈ZN |     |         |                |          |
|                                                     |       |         |                |                       |                   |                                                   |     |                        |     |         |                | ofN ele- |
|                                                     |       |         |                |                       |                   |                                                   |     | p                      |     |         |                | p        |
|                                                     |       |         |                |                       |                   | mentstoringelementsvˆ∈A                           |     |                        |     | anduˆ∈A | ,respectively. |          |
| [57] XiaoyongZhu,GeorgeIordanescu,IliaKarmanovi,and |       |         |                |                       |                   |                                                   |     |                        | N,p |         | N,p            |          |
Theproductpolynomialvˆ·uˆ∈A
MazenZawaideh. Usingmicrosoftaitobuildalung- N,p decodestotheHadamard
diseasepredictionmodelusingchestx-rayimages. productbetweenthevectorsvandu.Inthecontextofencryp-
tion,theSIMDtechniquecanamortizethecostofhomomor-
|     |     |     |     |     |     | phic multiplication |     | by a | factor of | 1/N. However,once |     | the |
| --- | --- | --- | --- | --- | --- | ------------------- | --- | ---- | --------- | ----------------- | --- | --- |
A ThreatModelandSecurity SIMD-encodedvectorisencrypted,itisnotstraightforward
tomanipulatethepositionsoftheencodedvalues.Forexam-
Weprovidesecurityagainstastaticsemi-honestprobabilis- ple,tohomomorphicallyright-hand-siderotatetheencrypted
tic polynomial time adversary A following the simulation vectorby k∈[1,N) unit,one needs to multiply the cipher-
textwitharotationkeygivenasRLWEN,q,p(ρ
| paradigm | [11,22,38]. | That | is,a | computationally | bounded |     |     |     |     |     |     | (sk)) |
| -------- | ----------- | ---- | ---- | --------------- | ------- | --- | --- | --- | --- | --- | --- | ----- |
sk 5kmod2N
adversaryA corruptseitherAlice(Server)orBob(Client)at where the automorphism : A (cid:55)→ A is defined by
|               |       |          |     |             |              |                          |     |     | ρ g | N,p | N,p |     |
| ------------- | ----- | -------- | --- | ----------- | ------------ | ------------------------ | --- | --- | --- | --- | --- | --- |
| the beginning | ofthe | protocol | Π   | and follows | the protocol |                          |     |     |     |     |     |     |
|               |       |          |     | F           |              | ρ (aˆ(X))=aˆ(Xg)modXN+1. |     |     |     |     |     |     |
g
specificationhonestly.Securityismodeledbydefiningtwo
interactions:arealinteractionwhereAliceandBobexecute
C FullVersionofHomCONV
| theprotocolΠ | F inthepresenceofA |     |     | andtheenvironmentE |     |     |     |     |     |     |     |     |
| ------------ | ------------------ | --- | --- | ------------------ | --- | --- | --- | --- | --- | --- | --- | --- |
andanidealinteractionwherethepartiessendtheirinputs
toatrustedpartythatcomputesthefunctionalityFfaithfully. WenowpresentthefullversionofHomCONVinFigure11.
SecurityrequiresthatforeveryadversaryA intherealinter- InStep1andStep2ofFigure11,Bobfirstpartitionsitsshare
action,thereisanadversarySim(calledthesimulator)inthe oftensor(withzero-padding)intosmallerblocksofthesame
| idealinteraction,suchthatnoenvironmentE |     |     |     |     | candistinguish |          |      |                               |     |     |     |         |
| --------------------------------------- | --- | --- | --- | --- | -------------- | -------- | ---- | ----------------------------- | --- | --- | --- | ------- |
|                                         |     |     |     |     |                | shapeC w | ×W w | ×H w alongthethreedimensions. |     |     |     | Bobthen |
betweenrealandidealinteractions. sendstoAliced d d RLWEciphertextsthateachofthem
C H W
Werecapthedefinitionofacryptographicinferenceproto- encrypts one partition blockof(cid:104)T(cid:105)B in Step 3. In the next
colinDELPHI[41].TheserverholdsamodelW consisting twosteps,Alicefirstpartitionsitsshare(cid:104)T(cid:105)A followingthe
ofd layersW ,···,W .Theclientholdsaninputvectorx. samepartitioningmannerinStep1andStep2.AfterthatAl-
1 d
|     |     |     |     |     |     | icepartitionsthekernelKintod |     |     |     | d non-overlappingblocks |     |     |
| --- | --- | --- | --- | --- | --- | ---------------------------- | --- | --- | --- | ----------------------- | --- | --- |
M C
Definition1 AprotocolΠbetweenaserverhavingasinput ThenAlicecanencodeeachofthemusingπw withaniden-
conv
modelparametersW =(W 1 ,...,W d )andaclienthavingas ticalparameterO w thatisbecausethetensorTispartitioned
inputafeaturevectorxisacryptographicinferenceprotocol intoblocksofthesameshapeC ×H ×W .Onreceiving
|     |     |     |     |     |     |     |     |     | w   | w   | w   |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
ifitsatisfiesthefollowingguarantees. the RLWE ciphertexts from Bob,Alice then computes the

|     |     |     |     |     |     |     | (cid:16) |     |     | (cid:17) |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | -------- | --- | --- | -------- | --- | --- | --- | --- | --- |
InputsandOutputs(cid:104)T(cid:48)(cid:105)A,(cid:104)T(cid:48)(cid:105)B←HomCONV {(cid:104)T(cid:105)A,K},{(cid:104)T(cid:105)B,sk} suchthat(cid:104)T(cid:105)A,(cid:104)T(cid:105)B∈ZC×H×W,K∈ZM×C×h×h
|                                                   |     |     |     |     |     |     |     |     |     |     |     |     | p   | p   |     |
| ------------------------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| andT(cid:48)=Conv2D(T,K;s)∈ZM×H(cid:48)×W(cid:48) |     |     |     |     |     | .   |     |     |     |     |     |     |     |     |     |
p
PublicParameters:pp=(HE.pp,pk,M,C,H,W,h,s).
h2
• Shape meta M,C,H,W,h such that ≤N and stride s>0. The optimal sizes of the partition winodws that minimize
argmin (cid:100) C (cid:101)(cid:100) H−h+1 (cid:101)(cid:100)W−h+1(cid:101)suchthath≤H ≤H,h≤W ≤W andH W ≤N.
|     |     | Hw,Ww (cid:98)N/(HwWw)(cid:99) |     | Hw−h+1 |     | Ww+h−1 |     |     | w   | w   |     | w   | w   |     |     |
| --- | --- | ------------------------------ | --- | ------ | --- | ------ | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|     |     |                                |     |        |     |        |     |     |     | N   |     |     | N   |     |     |
• ThepartitionwindowsizealongtheC-axisandM-axisisC w =min(C,(cid:98) (cid:99))andM w =min(M,(cid:98) (cid:99)).
|     |     |     |     |     |     |     |     |     |     | HwWw |     |     | CwHwWw |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---- | --- | --- | ------ | --- | --- |
• Setd =(cid:100) M (cid:101),d =(cid:100) C (cid:101),d =(cid:100) H−h+1 (cid:101)andd =(cid:100)W−h+1(cid:101).O =H W (M C −1)+W (h−1)+h−1.
|                                                                              | M   | Mw  | C   | Cw  | H   | Hw−h+1                              | W   | Ww−h+1 | w                        | w   | w w | w   | w   |     |     |
| ---------------------------------------------------------------------------- | --- | --- | --- | --- | --- | ----------------------------------- | --- | ------ | ------------------------ | --- | --- | --- | --- | --- | --- |
| SetH(cid:48)=(cid:98)H−h+s(cid:99),W(cid:48)=(cid:98)W−h+s(cid:99),H(cid:48) |     |     |     |     |     | =(cid:98)Hw−h+s(cid:99)andW(cid:48) |     |        | =(cid:98)Ww−h+s(cid:99). |     |     |     |     |     |     |
| •                                                                            |     |     |     |     |     | w                                   |     | w      |                          |     |     |     |     |     |     |
|                                                                              |     | s   |     |     | s   |                                     | s   |        |                          | s   |     |     |     |     |     |
(cid:10) (cid:11)B
1: Bobfirstpartitions(cid:104)T(cid:105)BintoblocksalongtheH-axisandW-axis T ∈ZC ×Hw×Ww forα∈[[d ]]andβ∈[[d ]].Each
|     |     |                    |     |     |     |     |     |     |     | α,β | q   |     | H                  | W   |     |
| --- | --- | ------------------ | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ------------------ | --- | --- |
|     |     | (cid:10) (cid:11)B |     |     |     |     |     |     |     |     |     |     | (cid:10) (cid:11)B |     |     |
block T consistsofH continuousrowsandW continuouscolumnsof(cid:104)T(cid:105)B.Indeed, T istakenfromthe
|     |     | α,β |     |     | w   |     |     | w   |     |     |     |     | α,β |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
(cid:10) (cid:11)B
α(H −h+1)-throwandβ(W −h+1)-thcolumnof(cid:104)T(cid:105)B.Zero-paddingmightbeusedtomakesureall T blocks
|     | w   |     |     |     | w   |     |     |     |     |     |     |     |     | α,β |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
containthesamenumberofrowsandcolumns.
|     |     |     |     |     |     |     | (cid:10) | (cid:11)B |     |     |     | (cid:10) | (cid:11)B |     |     |
| --- | --- | --- | --- | --- | --- | --- | -------- | --------- | --- | --- | --- | -------- | --------- | --- | --- |
2: Bobthensplitsthechannelsofeachblocktensor T intonon-overlappingblocks T ∈ZC w×Hw×Ww forγ∈[[d ]].
|     |     |     |     |     |     |     |     | α,β                |     |     |     | γ,α,β | p   |     | C   |
| --- | --- | --- | --- | --- | --- | --- | --- | ------------------ | --- | --- | --- | ----- | --- | --- | --- |
|     |     |     |     |     |     |     |     | (cid:10) (cid:11)B |     |     |     |       |     |     |     |
Also,zero-paddingmightbeusedtomakesureall T blockscontainthesamenumberofchannels.
γ,α,β
|     |     |     |     |     |     |     |     |     | =RLWEN | ,q,p(πi | (cid:10) |     | (cid:11)B |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ------ | ------- | -------- | --- | --------- | --- | --- |
3: BobencryptsandthensendstheRLWEciphertexts{CT ( T ))}toAlice.
|     |     |     |     |     |     |          |           | γ,α,β |     | pk  | conv | γ,α,β |     |     |     |
| --- | --- | --- | --- | --- | --- | -------- | --------- | ----- | --- | --- | ---- | ----- | --- | --- | --- |
|     |     |     |     |     |     | (cid:10) | (cid:11)A |       |     |     |      |       |     |     |     |
Alicepartitions(cid:104)T(cid:105)A intoblocks T ∈ZC w×Hw×Ww followingthesamemannerinStep1andStep2.ThenAlice
| 4:  |                                  |     |     |     |     | γ,α,β | p                         |              |           |     |     |     |     |     |     |
| --- | -------------------------------- | --- | --- | --- | --- | ----- | ------------------------- | ------------ | --------- | --- | --- | --- | --- | --- | --- |
|     | encodeseachblocktoapolynomialvia |     |     |     |     |       | (cid:10) tˆ (cid:11)A =πi | ( (cid:10) T | (cid:11)A | ).  |     |     |     |     |     |
|     |                                  |     |     |     |     |       | γ,α,β                     | conv         | γ,α,β     |     |     |     |     |     |     |
5: Alice then splits K into sub-kernels along the M-axis, i.e., K ∈ZM w×C×h×h for θ∈[[d ]]. Then Alice further split
|     |     |     |     |     |     |     |     |     | θ   | p   |     |     | M   |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
∈ZM w×Cw×h×h
each K into smaller block along the C-axis, i.e., K θ,γ for γ∈[[d C ]]. Zero-padding might be used to
|     |     | θ   |     |     |     |     |     |     | p   |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
makesureallblockscontainsthesamenumberofelements.ThenAliceencodestheseblocktensorsintopolynomials
kˆ =πw
|     | θ,γ                                            | conv (K | θ,γ ,O w | ).  |                      |                                |     |     |     |     |     |     |     |     |     |
| --- | ---------------------------------------------- | ------- | -------- | --- | -------------------- | ------------------------------ | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|     | Alicesamples(cid:104)T(cid:48)(cid:105)AfromZM |         |          |     | ×H(cid:48)×W(cid:48) | uniformlyatrandomandoutputsit. |     |     |     |     |     |     |     |     |     |
| 6:  |                                                |         |          |     | p                    |                                |     |     |     |     |     |     |     |     |     |
Onreceiving{CT },AlicecomputesCT(cid:48) =(cid:1) (CT (cid:1)(cid:10) tˆ (cid:11)A )(cid:2)kˆ forθ∈[[d ]],α∈[[d ]]andβ∈
| 7:  |         |     | γ,α,β |     |     |     | θ,α,β | γ∈[[dC]] | γ,α,β | γ,α,β |     | θ,γ | M   | H   |     |
| --- | ------- | --- | ----- | --- | --- | --- | ----- | -------- | ----- | ----- | --- | --- | --- | --- | --- |
|     | [[d ]]. |     |       |     |     |     |       |          |       |       |     |     |     |     |     |
W
[ExtratandRe-mask.]Foreachc(cid:48)∈[[M]],i(cid:48)∈[[H(cid:48)]],and j(cid:48)∈[[W(cid:48)]],AlicesendsanLWEciphertexttoBobct =
| 8:  |     |     |     |     |     |     |     |     |     |     |     |     |     |     | c(cid:48),i(cid:48),j(cid:48) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ----------------------------- |
Extract(CT(cid:48) ,O −cC H W +isH +js)(cid:12)(cid:104)T(cid:48)(cid:105)A[c(cid:48),i(cid:48),j(cid:48)],wheretheindexofCT(cid:48) iscalculatedasθ=(cid:98)c(cid:48)/M (cid:99),
|     |     | θ,α,β | w   | w   | w w | w   |     |     |     |     |     | θ,α,β |     |     | w   |
| --- | --- | ----- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ----- | --- | --- | --- |
α=(cid:98)i(cid:48)s/(H −h+1)(cid:99),and β=(cid:98)j(cid:48)s/(W −h+1)(cid:99). The position of the extracting coefficient is determined by c=
|     |                | w            |              |     |                                                                          |                         | w   |     |                      |                                                                       |     |     |     |     |     |
| --- | -------------- | ------------ | ------------ | --- | ------------------------------------------------------------------------ | ----------------------- | --- | --- | -------------------- | --------------------------------------------------------------------- | --- | --- | --- | --- | --- |
|     | c(cid:48) modM | ,i=i(cid:48) | modH(cid:48) |     | and j=                                                                   | j(cid:48) modW(cid:48). |     |     |                      |                                                                       |     |     |     |     |     |
|     |                | w            |              | w   |                                                                          |                         | w   |     |                      |                                                                       |     |     |     |     |     |
|     |                |              |              |     | c(cid:48),i(cid:48),j(cid:48)},Boboutputs(cid:104)T(cid:48)(cid:105)B∈ZM |                         |     |     | ×H(cid:48)×W(cid:48) | where(cid:104)T(cid:48)(cid:105)B[c(cid:48),i(cid:48),j(cid:48)]=LWE− |     |     |     |     |     |
9: Onreceivingtheciphertexts{ct 1(ct c(cid:48),i(cid:48),j(cid:48)).
|     |     |     |     |     |     |     |     |     | p   |     |     |     | sk  |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
Figure11:ProposedSecureConvolutionProtocol(FullVersion)
ofFigure1bforthefieldF=
secure convolution using d d d d homomorphic multi- theidealfunctionalityF
|     |     |     |     | M C | H W |     |     |     |     |     |     | CONV |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---- | --- | --- | --- |
plications and homomorphic additions. Indeed,the RLWE Z andforh2≤N inpresenceofasemi-honestadmissible
p
ciphertextCT(cid:48)
|     |     |     | inStep7correspondstotheconvolution |     |     |     |     |     | adversary. |     |     |     |     |     |     |
| --- | --- | --- | ---------------------------------- | --- | --- | --- | --- | --- | ---------- | --- | --- | --- | --- | --- | --- |
θ,α,β
| oftheblocktensorT            |     |     | andthesub-kernelsK |                |     |     | .Asaresult,        |      |     |     |     |     |     |     |     |
| ---------------------------- | --- | --- | ------------------ | -------------- | --- | --- | ------------------ | ---- | --- | --- | --- | --- | --- | --- | --- |
|                              |     |     | α,β                |                |     |     | θ                  |      |     |     |     |     |     |     |     |
| eachRLWEciphertextCT(cid:48) |     |     |                    | obtainsatmostM |     |     | H(cid:48)W(cid:48) | val- |     |     |     |     |     |     |     |
|                              |     |     |                    | θ,α,β          |     |     | w w w              |      |     |     |     |     |     |     |     |
uesofT(cid:48)initsencryptedcoefficients.Finally,Aliceextracts
|     |     |     |     |     |     |     |     |     | D Proofs |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | -------- | --- | --- | --- | --- | --- | --- |
MH(cid:48)W(cid:48)LWEciphertextsthateachofthemencryptsoneentry
oftheoutputtensorT(cid:48).Similartothebasicversion,inStep8
|     |     |     |     |     |     |     |     |     | Proof3(Proposition2) |     |     | WewriteO(cid:48)=O−c(cid:48)CHW |     |     | forsim- |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | -------------------- | --- | --- | ------------------------------- | --- | --- | ------- |
AlicerandomizestheencryptedvaluesintheLWEciphertexts
plicity.Bythedefinition(1)wehave
byhomomorphicallyaddinguniformrandomvaluesbefore
sendingbacktheLWEciphertextstoBobfordecryption.
|          |     |                                      |     |     |     |     |     |     |                |       | tˆ[d]kˆ[x−d]− |     | tˆ[d]kˆ[N+x−d] |     |     |
| -------- | --- | ------------------------------------ | --- | --- | --- | --- | --- | --- | -------------- | ----- | ------------- | --- | -------------- | --- | --- |
|          |     |                                      |     |     |     |     |     |     | tˆ(cid:48)[x]= | ∑     |               |     | ∑              |     | (6) |
| Theorem4 |     | TheprotocolHomCONVinFigure11realizes |     |     |     |     |     |     |                | 0≤d≤x |               |     | x<d<N          |     |     |

forallx∈[[N]].Sincetˆ[x]iszeroforallx≥CHW andthe Table9:DNNArchitectures.
targetpositionO(cid:48)+i(cid:48)sW+j(cid:48)s>CHW,wethushave
|                                               |     |     |                                             |     |     |     |          |     | linearoperations |     |     | non-linearoperations |     |       |
| --------------------------------------------- | --- | --- | ------------------------------------------- | --- | --- | --- | -------- | --- | ---------------- | --- | --- | -------------------- | --- | ----- |
| tˆ(cid:48)[O(cid:48)+i(cid:48)sW+j(cid:48)s]= |     | ∑   | tˆ[d]kˆ[O(cid:48)+i(cid:48)sW+j(cid:48)s−d] |     |     |     | Networks |     |                  |     |     |                      |     |       |
|                                               |     |     |                                             |     |     |     |          |     | CONV             | BN  | FC  | ReLU-then-Trunc      |     | Trunc |
d<CHW
|     |     |     |     |     |     |     | MNet |     | 7   | 0   | 1   | 7   |     | 0   |
| --- | --- | --- | --- | --- | --- | --- | ---- | --- | --- | --- | --- | --- | --- | --- |
=∑tˆ[cHW+iW+j]kˆ[O(cid:48)+i(cid:48)sW+j(cid:48)s−(cHW+iW+j)]
|     |     |     |     |     |     |     | RN32 |     | 34  | 34  | 1   | 31  |     | 37  |
| --- | --- | --- | --- | --- | --- | --- | ---- | --- | --- | --- | --- | --- | --- | --- |
c,i,j
=∑tˆ[cHW+iW+j]kˆ[O(cid:48)−cHW−(i−i(cid:48)s)W−(j−j(cid:48)s)] SqNet 26 0 0 26 0
|     |     |     |     |     |     |     | RN50 |     | 53  | 49  | 1   | 49  |     | 49  |
| --- | --- | --- | --- | --- | --- | --- | ---- | --- | --- | --- | --- | --- | --- | --- |
c,i,j
|     |     |     |     |     |     |     | DNet |     | 121 | 121 | 0   | 121 |     | 120 |
| --- | --- | --- | --- | --- | --- | --- | ---- | --- | --- | --- | --- | --- | --- | --- |
tˆ[cHW+(i(cid:48)s+l)W+j(cid:48)s+l(cid:48)]kˆ[O(cid:48)−cHW−lW−l(cid:48)]
= ∑
MNet=MiniONN;RN32=ResNet32;RN50=ResNet50
c,i(cid:48),j(cid:48)
SqNet=SqueezeNet;DNet=DenseNet121
| Thelastlinereplacesi=i(cid:48)s+land |     |     |     | j= j(cid:48)s+l(cid:48).Also,accord- |     |     |     |     |     |     |     |     |     |     |
| ------------------------------------ | --- | --- | --- | ------------------------------------ | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
ingtothedefinitionofπw ,thevaluekˆ[O(cid:48)−cHW−lW−l(cid:48)] Inputs&Outputs:(cid:104)z(cid:105)A,(cid:104)z(cid:105)B←AND (cid:16) (cid:104)x(cid:105)A,(cid:104)x(cid:105)B,(cid:104)y(cid:105)A,(cid:104)y(cid:105)B (cid:17)
conv
|     |     |     |     |     |     |     |     |     |     | 2   | 2   | 2   | 2   | 2 2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
iszerowhenl,l(cid:48)∈/[[h]].Thus,weonlyneedtotakecareof s.t.x,y,z∈{0,1}andz=x∧y.
thepositionsthatl,l(cid:48)∈[[h]].Theaboveequationcontinues.
AliceandBobjointlygenerateabeavertriple:(cid:104)c(cid:105)A⊕(cid:104)c(cid:105)B=
1:
2 2
∑ tˆ[cHW+(i(cid:48)s+l)W+j(cid:48)s+l(cid:48)]kˆ[O(cid:48)−cHW−lW−l(cid:48)] ((cid:104)a(cid:105)A ⊕(cid:104)a(cid:105)B )∧((cid:104)b(cid:105)A ⊕(cid:104)b(cid:105)B ).
| =       |     |     |     |     |     |     |     | 2                                 | 2   | 2   | 2                     |                                               |                       |                       |
| ------- | --- | --- | --- | --- | --- | --- | --- | --------------------------------- | --- | --- | --------------------- | --------------------------------------------- | --------------------- | --------------------- |
|         |     |     |     |     |     |     |     | Alicecomputes(cid:104)e(cid:105)A |     |     | =(cid:104)x(cid:105)A | ⊕(cid:104)a(cid:105)A and(cid:104)f(cid:105)A | =(cid:104)y(cid:105)A | ⊕(cid:104)b(cid:105)A |
| c∈[[C]] |     |     |     |     |     |     | 2:  |                                   |     | 2   | 2                     | 2                                             | 2                     | 2 2 .                 |
l,l(cid:48)∈[[h]]
Bobcomputes(cid:104)e(cid:105)B=(cid:104)x(cid:105)B⊕(cid:104)a(cid:105)Band(cid:104)f(cid:105)B=(cid:104)y(cid:105)B⊕(cid:104)b(cid:105)B.
|     |     |     |     |     |     |     |     |     |     | 2   | 2   | 2   | 2   | 2 2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
= ∑ T[c,i(cid:48)s+l,j(cid:48)s+l(cid:48)]kˆ[O−c(cid:48)CHW−cHW−lW−l(cid:48)] 3: AliceandBobopeneand f.
Alicecomputes(cid:104)z(cid:105)A=((cid:104)a(cid:105)A·f)⊕((cid:104)b(cid:105)A·e)⊕(cid:104)c(cid:105)A,andBob
| c∈[[C]] |     |     |     |     |     |     | 4:  |     |     | 2   | 2   | 2   |     | 2   |
| ------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
l,l(cid:48)∈[[h]] computes(cid:104)z(cid:105)B=(e·f)⊕((cid:104)a(cid:105)B·f)⊕((cid:104)b(cid:105)B·e)⊕(cid:104)c(cid:105)B
|     |     |     |     |     |     |     |     |     |     | 2   |     | 2   | 2   | 2   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
= ∑ T[c,i(cid:48)s+l,j(cid:48)s+l(cid:48)]K[c(cid:48),c,l,l(cid:48)]
| c∈[[C]] |     |     |     |     |     |     |     |     | Figure12:ProtocolforF |     |     | AND | .   |     |
| ------- | --- | --- | --- | --- | --- | --- | --- | --- | --------------------- | --- | --- | --- | --- | --- |
l,l(cid:48)∈[[h]]
|     |     |     |     |     |     |     |     |     |     |     |     | (cid:16) |     | (cid:17) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | -------- | --- | -------- |
ThefinallineisexactlyT(cid:48)[c(cid:48),i(cid:48),j(cid:48)]. (cid:4) InputsandOutputs:(cid:104)d(cid:105)A ,(cid:104)d(cid:105)B ←B2A (cid:104)c(cid:105)A,(cid:104)c(cid:105)B,f such
|     |     |     |     |     |     |     |     |     |     |     | 2f 2f |     | 2   | 2   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ----- | --- | --- | --- |
thatc∈{0,1}andd=c.
|     |     | The correctness |     | of  | Theorem | 2 is di- |     |     |     |     |     |     |     |     |
| --- | --- | --------------- | --- | --- | ------- | -------- | --- | --- | --- | --- | --- | --- | --- | --- |
Proof4(Theorem2.)
|                                                   |     |     |     |     |     |     |     | AliceandBobinvokeaninstanceof |     |     |     | (cid:0)2 (cid:1) -COTf,whereAlice |     |     |
| ------------------------------------------------- | --- | --- | --- | --- | --- | --- | --- | ----------------------------- | --- | --- | --- | --------------------------------- | --- | --- |
| rectlyderivedfromProposition2.Wenowshowthethepri- |     |     |     |     |     |     | 1:  |                               |     |     |     | 1                                 |     |     |
isthesenderwithcorrelationfunctiong(x)=x−2(cid:104)c(cid:105)A
| vacypart. |     |     |     |     |     |     |     |     |     |     |     |     |     | and |
| --------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
2
(CorruptedAlice.)Alice’sviewofViewH omCONV Bobisthereceiverwithinputchoice(cid:104)c(cid:105)B .Alicelearnsxand
|     |     |     |     |     | consistsof |     |     |     |     |     |     | 2   |     |     |
| --- | --- | --- | --- | --- | ---------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
A
| anRLWEciphertextCT(cid:48).ThesimulatorSim |     |     |     |     | forthisview |     |     | Boblearnsy.                       |     |     |                       |                                       |     |      |
| ------------------------------------------ | --- | --- | --- | --- | ----------- | --- | --- | --------------------------------- | --- | --- | --------------------- | ------------------------------------- | --- | ---- |
|                                            |     |     |     |     | A           |     |     | Alicecomputes(cid:104)d(cid:105)A |     |     | =(cid:104)c(cid:105)A | −x,andBobcomputes(cid:104)d(cid:105)B |     |      |
| canbeconstructedasfollows.                 |     |     |     |     |             |     | 2:  |                                   |     | 2f  |                       |                                       |     | 2f = |
2
(cid:104)c(cid:105)B+y.
2
| 1. Giventheaccesstometa,Sim |     |     |     | outputstheciphertext |     |     |     |     |     |     |     |     |     |     |
| --------------------------- | --- | --- | --- | -------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
A
(cid:48)
| C(cid:102)T | =RLWEN,q(0)toAlice. |     |     |     |     |     |     |     | Figure13:B2AProtocol. |     |     |     |     |     |
| ----------- | ------------------- | --- | --- | --- | --- | --- | --- | --- | --------------------- | --- | --- | --- | --- | --- |
pk
| The security                                        | against | a corrupted |     | Alice (Server) | is  | directly |                                |     |     |     |     |                                 |                                          |     |
| --------------------------------------------------- | ------- | ----------- | --- | -------------- | --- | -------- | ------------------------------ | --- | --- | --- | --- | ------------------------------- | ---------------------------------------- | --- |
|                                                     |         |             |     |                |     |          | Similarly,theLWEciphertexts{ct |     |     |     |     | c(cid:48),i(cid:48),j(cid:48)}≈ | {c˜t c(cid:48),i(cid:48),j(cid:48)}dueto |     |
| reducedtothesemanticsecurityoftheunderlyencryption. |         |             |     |                |     |          |                                |     |     |     |     |                                 | c                                        |     |
ThuswehaveViewHomCONV≈ Sim (meta). thesemanticsecurity. Also,thevaluesin theoutputtensor
|     |     | A   | c   | A   |     |     |     |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
(Corrupted Bob.) Bob’s view of ViewH omCONV consists of (cid:104)T(cid:48)(cid:105)BofBobinHomCONVdistributeuniformlyinZ which
|     |     |     |     | B   |     |     |     |     |     |     |     |     |     | p   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
samplesT˜.Thuswehave
LWEciphertexts{ct c(cid:48),i(cid:48),j(cid:48)},andthedecryptionoftheseLWE isexactthesamedistributionSim B
ciphertexts,i.e.,(cid:104)T(cid:48)(cid:105)B.ThesimulatorSim ViewH omCONV≈ Sim (meta,out). (cid:4)
|     |     |     |     | C   | forthisviewcan |     |     | B   | c   | B   |     |     |     |     |
| --- | --- | --- | --- | --- | -------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
beconstructedasfollows.
ThesecurityproofsfortheTheorems13and4canbegiven
| 1. On                    | receiving | the RLWE | ciphertext | CT                   | from | Bob and | inasimilarmanner. |     |     |     |     |     |     |     |
| ------------------------ | --------- | -------- | ---------- | -------------------- | ---- | ------- | ----------------- | --- | --- | --- | --- | --- | --- | --- |
| giventheaccesstometa,Sim |           |          |            | samplesuniformrandom |      |         |                   |     |     |     |     |     |     |     |
B
|                                                      |     | andcomputesC(cid:102)T=RLWEN |     |                             |     | ,q(rˆ). |                                           |               |     |     |      |       |     |        |
| ---------------------------------------------------- | --- | ---------------------------- | --- | --------------------------- | --- | ------- | ----------------------------------------- | ------------- | --- | --- | ---- | ----- | --- | ------ |
| polynomialrˆ∈A                                       |     |                              |     |                             |     |         | E                                         | ProtocolsforF |     |     | andF | 2 f   |     |        |
|                                                      |     | N,p                          |     |                             |     | pk      |                                           |               |     |     | AND  | B 2 A |     |        |
| 2. Foreachc(cid:48)∈[[M]],i(cid:48)∈[[H(cid:48)]]and |     |                              |     | j(cid:48)∈[[W(cid:48)]],Sim |     | out-    |                                           |               |     |     |      |       |     |        |
|                                                      |     |                              |     |                             |     | B       | WedescribetheclassicprotocolforcomputingF |               |     |     |      |       |     | inFig- |
| putsanLWEciphertextc˜t                               |     |                              |     |                             |     |         |                                           |               |     |     |      |       |     | AND    |
c(cid:48),i(cid:48),j(cid:48) =Extract(C(cid:102)T)toBob. ure12,wherebeavertriplesaregeneratedwith (cid:0)2(cid:1) -ROT [3].
1
1
outputsthetensorT˜ WedescribeaprotocolforF2f inFigure13,whichisalso
| 3. Giventheaccesstoout,Sim |     |     | B   |     |     | such |     |     |     |     | B2A |     |     |     |
| -------------------------- | --- | --- | --- | --- | --- | ---- | --- | --- | --- | --- | --- | --- | --- | --- |
(cid:0)2(cid:1)
that T˜[c(cid:48),i(cid:48),j(cid:48)]=rˆ[O−c(cid:48)CHW +i(cid:48)sW + j(cid:48)s] for each usedinCryptoFlow2[46,48],exceptthat -COT isinstan-
|     |     |     |     |     |     |     |     |     |     |     |     |     | 1   | f   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
c(cid:48)∈[[M]],i(cid:48)∈[[H(cid:48)]]and j(cid:48)∈[[W(cid:48)]]. tiatedwithVOLE-styleOT.