<!-- Volume 108, Number 4, July-August 2003 -->

<!-- Journal of Research of the National Institute of Standards and Technology -->

[J. Res. Natl. Inst. Stand. Technol. 108, 249-265 (2003)]

# Review of Instrumented Indentation


| Volume 108  | Number 4  | July-August 2003  |
| --- | --- | --- |
| Mark R. VanLandingham1<br>National Institute of Standards<br>and Technology,<br>Gaithersburg, MD 20899-8610<br>mark.vanlandingham@us.army.mil | Instrumented indentation, also known as<br>depth-sensing indentation or nanoindenta<br>tion, is increasingly being used to probe<br>the mechanical response of materials from<br>metals and ceramics to polymeric and<br>biological materials. The additional levels<br>of control, sensitivity, and data acquisition<br>offered by instrumented indentation<br>systems have resulted in numerous<br>advances in materials science, particularly<br>regarding fundamental mechanisms of<br>mechanical behavior at micrometer and<br>even sub-micrometer length scales.<br>Continued improvements of instrumented<br>indentation testing towards absolute<br>quantification of a wide range of material<br>properties and behavior will require<br>advances in instrument calibration,<br>measurement protocols, and analysis tools<br>and techniques. In this paper, an overview  | of instrumented indentation is given with regard to current instrument technology<br>and analysis methods. Research efforts at the National Institute of Standards and<br>Technology (NIST) aimed at improving<br>the related measurement science are<br>discussed.<br>Key words: calibration methods; contact mechanics; depth-sensing indentation;<br>elastic modulus; instrumented indentation;measurement science; nanoindentation;<br>tip shape characterization..<br>Accepted: July 29, 2003<br>Available online: http://www.nist.gov/jres |


## 1.Introduction

Indentation or hardness testing has long been used for characterization and quality control of materials,but the results are not absolute and depend on the test method. In general, traditional hardness tests consist of the application of a single static force and correspon ding dwell time with a specified tip shape and tip material, resulting in a hardness impression that has dimensions on the order of millimeters. The output of these hardness testers is typically a single indentation hardness value that is a measure of the relative pene tration depth of the indentation tip into the sample. For example, the Rockwell hardness scales are distin guished by the amount of static force applied (e.g.,100 kg for Rockwell B compared to 150 kg for Rockwell C); the tip shape (e.g., a spherical tip with a diameter of 1.6 mm for Rockwell B compared to a conical tip that has a spherical apex with a radius of 200 µm for Rockwell C); and the tip material (e.g., steel for Rockwell B compared to diamond for Rockwell C)[1]. Harder metals are more appropriately characterized using higher forces and/or pyramidal tips, whereas lower forces and spherical tips are used on softer metals. Similarly, different durometers, which are used to characterize the mechanical resistance of polymers,have different spring constants and either a flat conical tip, a sharp conical tip, or a spherical tip, as specified in ASTM D 2240 Standard Test Method for Rubber Property—Durometer Hardness. Durometers with higher spring constants and sharp tips can be used to evaluate stiffer polymers compared to durometers with lower spring constants and/or flat or spherical tips.

 Current affiliation: Army Research Laboratory,

Aberdeen Proving Ground, MD 21005.

<!-- 249 -->

<!-- Volume 108, Number 4, July-August 2003 -->

<!-- Journal of Research of the National Institute of Standards and Technology -->

Instrumented indentation, also known as depth sensing indentation or nanoindentation, is increasingly being used to probe the mechanical response of materi als from metals and ceramics to polymeric and bio logical materials. In contrast to traditional hardness testers, instrumented indentation systems allow the application of a specified force or displacement history,such that force, $P$ , and the displacement, $h$ , are con trolled and/or measured simultaneously and continu ously over a complete loading cycle. Additionally, the extremely small force and displacement resolutions,often as low $\text {as}\approx 1μ\mathrm {\sim N}$  and $\approx 0.2$  nm, respectively, or lower for some systems, are combined with very large ranges of applied forces and displacements (tens of $N$  to hundreds of mN or larger in force and tens of nm to tens of $μm$  or larger in displacement) to allow a single instrument to be used to characterize nearly all types of material systems. Recent developments include improved user control over loading histories, improved system and software robustness allowing much higher levels of test automation, and the use of dynamic oscillation for improved sensitivity and additional testing capabilities.

The additional levels of control, sensitivity, and data acquisition offered by instrumented indentation systems have resulted in numerous advances in materi als science, particularly regarding fundamental mecha nisms of mechanical behavior at micrometer and even sub-micrometer length scales. Instrumented indentation systems have been used to study, for example, disloca tion behavior in metals [2-4], fracture behavior in ceramics [5-6], mechanical behavior of thin films [7-10] and bone [11], residual stresses [12], and time dependent behavior in soft metals [13-15] and poly mers [16-22]. Additionally, lateral probe motion is also being incorporated to explore tribological behavior of surfaces, including scratch resistance of coatings [23, 24] and wear resistance of metals [25]. The extent to which these techniques can be used to quantify macroscopic material properties is continually being explored. Indentation values of elastic modulus are routinely calculated and compared to values from macroscopic mechanical tests. Further, a number of researchers are utilizing techniques such as dimension al analysis and finite element modeling to relate mate rial constitutive behavior to indentation force-displace ment data, and even to predict stress-strain behavior based on instrumented indentation data [26, 27].Continued improvements of instrumented indenta tion testing towards absolute quantification and standardization for a wide range of material properties and behavior will require advances in instrument calibration, measurement protocols, and analysis tools and techniques. In this paper, an overview of instru mented indentation is given with regard to current instrument technology and analysis methods. Research efforts at the National Institute of Standards and Technology (NIST) are then discussed, which are aimed at improving the related measurement science.

## 2.Overview of Instrumented Indentation

### 2.1 Instrumentation

Many instrumented indentation systems can be generalized in terms of the schematic illustration shown in Fig. 1 [28,29]. Commercially available systems include those developed by Nano Instruments1 (Oak Ridge, TN; now part of MTS Systems Corp.) [28],Hysitron, Inc. (Minneapolis, MN) [30], Micro Materials Ltd. (UK) [31], CSIRO (Australia) [32], and CSEM (now CSM) Instruments (Switzerland) [23].Force is often applied using either electromagnetic or electrostatic actuation, and a capacitive sensor is typi cally used to measure displacement. In the MTS Nano Instruments, Hysitron, CSIRO, and CSM Instruments systems, the axis of the indenter is vertical (see Fig. 1),while in the Micro Materials system, it is horizontal.Also, the MTS Nano Instruments, Micro Materials,CSIRO, and CSM Instruments systems apply force and measure displacement through separate means, while the Hysitron system uses the same transducer for both force application and displacement measurement.Regardless of the operational differences, the raw force and raw displacement data for these systems are always coupled due to the leaf springs, and in fact, a plot of the raw force as a function of the raw displacement with the tip out of contact is characteristic of the spring stiffness. In the following sections, the measurement methods, analysis techniques, and calibration issues presented are applicable, in general, to current com mercial instrumented indentation systems.

1 Certain commercial equipment, instruments, or materials are iden tified in this paper to foster understanding. Such identification does not imply recommendation or endorsement by the National Institute of Standards and Technology, nor does it imply that the materials or equipment identified are necessarily the best available for the purpose.

<!-- 250 -->

<!-- Volume 108, Number 4, July-August 2003 -->

<!-- Journal of Research of the National Institute of Standards and Technology -->

<!-- Load Application Device -Springs Displacement Sensor Springs Probe Tip Sample Load Frame -->
![](https://web-api.textin.com/ocr_image/external/53c3cb88ec039622.jpg)

Fig.1. Schematic illustration of an instrumented indentation system.

### 2.2 Measurement Methods

Some of the earliest research related to the develop-ment of instrumented indentation is found in the early-to mid-1980's [29,31,33,34].Since that time,the con-tinuing evolution of computer technology has led to improved control over instrumented indentation testing.Although some specialized research instruments are displacement controlled (for example, the inter-facial force microscope [35]), most indentation systems are force-driven devices, such that the force history is most easily controlled with displacement control achieved using signal feedback. Typical force-time ( $P$ -t) and force-displacement (P-h) data are shown in Fig. 2. In Fig. 2a and Fig. 2b, indentation data taken using a constant loading rate, $9$ ,is shown for poly (methyl methacrylate), whereas in Fig. $2c$  and Fig. 2d,loading data are shown for constant $\dot {P}/P$ for poly-styrene. In both cases, the loading segment is followed by a hold segment, which is then followed by an unloading segment using a constant unloading rate. In Fig. 2c and Fig. 2d,a hold period near the end of the unloading segment is also shown. Assuming the mechanical behavior of the material is not a function of time, the ratio of loading rate, $P$ ,to force,P,has been related to a proposed expression for strain rate for an indentation measurement, $\dot {\varepsilon }_{i}$ ,through the follow-ing relation [36]:

$$\dot {\varepsilon }_{i}=\frac {\dot {h}}{h}=\frac {1}{\beta }\left(\frac {\dot {P}}{P}-\frac {\dot {H}}{H}\right)\tag{1}$$

Here, $H=P/A$ is the hardness, $\dot {H}=\mathrm {d}H$ /dt is the time rate of change during testing of the hardness, and $\beta$  describes the shape of an idealized indentation tip,where the cross-section area, A, is related to the

distance, $h$  from the tip apex by $A=\mathrm {ch}^{\beta }.$ Note that in Eq. (1), $\beta$  cannot be 0, so that the right side of this equation is not valid for flat punch geometry. For a tip-sample combination for which $H$  is constant with depth,constant $\dot {P}/P$  testing yields a constant indentation strain rate. For many materials, H is a function of $\dot {\varepsilon }_{i}$ which can then be characterized using these types of tests.Further, because $H=P/$  represents a mean pres-sure or stress during indentation,constant $\dot {P}/P$ testing could be used, for example, to study creep behavior under "constant H" (or equivalently, "constant mean pressure" or "constant mean stress") conditions in time-dependent materials.

A more ubiquitous test method used in force-controlled instrumented indentation employs the use of a constant loading rate, or for a displacement-controlled system, a constant displacement rate. In either case, no feedback is necessary, which lends to the simplicity of these methods. Of course, feedback could be used to produce a constant displacement rate in a force-controlled system or a constant loading rate in a displacement-controlled system. The former approach is perhaps more useful, because displacement, $h$ ,and displacement rate, $h$ , are linked to indentation strain and strain rate, whereas force and loading rate are more difficult to link to either stress or strain. For exam-ple, for conical or pyramidal tip geometry, a nominal indentation strain is related to the characteristic includ-ed angle or angles of the tip. Fora paraboloidal tip,indentation strain is related to the ratio of the contact radius to the tip radius, and the contact radius is direct-ly related to h [16,21]. For any tip geometry, the inden-tation strain rate canbe calculated from the ratio $\dot {}/$ as in Eq. (1). However, the mean stress or hardness, $H$ ,is the ratio of force, $P$  to contact area, A,which in gen-eral is related to displacement through the tip geometry.Only in the case of a flat punch, where A is constant with $h$ , is H a function of force only. As shown in Eq.(1), $\dot {P}/P$ can be related to indentation strain rate,but only through additional calculations of $\dot {H}$ and H.

Other quasi-static test methods that have been used to characterize time-dependent response are indentation creep tests [13-15,17,21] and indentation stress relax-ation tests [21]. As in a traditional tensile creep test,force is held constant in an indentation creep test and displacement or strain is monitored [1]. However, for the case of tensile creep, the change in cross-section area as the sample elongatesis typically small during most of the test, such that constant force is essentially equivalent to constant stress. In the indentation creep test, the gradual displacement of the tip into the sample causes a substantial change in the contact area, as

<!-- 251 -->

<!-- Volume 108, Number 4, July-August 2003 -->

<!-- Journal of Research of the National Institute of Standards and Technology -->

<!-- 100 80 Load (μN) 60 40 20 0 0 5 10 15 20 25 Time (s) -->
![](https://web-api.textin.com/ocr_image/external/e113d8076101571c.jpg)

(a)

<!-- 100 80 Load (mN) 60 40 20 0 0 30 60 90 120 Displacement (nm) -->
![](https://web-api.textin.com/ocr_image/external/3563a78b94d6a473.jpg)

(b)

<!-- 250 200 Load (mN) 150 100 50 0 0 100 200 300 400 Time (s) -->
![](https://web-api.textin.com/ocr_image/external/762fff8af00db98f.jpg)

(c)

(d)

<!-- 250 200 Load (mN) 150 100 50 0 0 3 6 9 12 Displacement (mm) -->
![](https://web-api.textin.com/ocr_image/external/b28b01505538fb0b.jpg)

Fig.2. Force-time (a and c) and corresponding force-displacement (b and d) indentation data: (a and b) data taken on poly(methyl methacrylate)using a constant P loading; (c and d) data taken on polystyrene using constant P/P loading. Both data sets include a 10 s hold period between loading and unloading, and the data in (c) and (d) include an additional hold period near the end of the unloading segment.

shown in Fig. 3, such that both the stress and the strain fields evolve during the test, complicating analysis and comparison to bulk measurements. For the indentation stress relaxation test, displacement is held constant (through feedback in a force-controlled system) and the gradual decrease in force is recorded. Because dis-placement is closely linked to strain in an indentation experiment, constant indentation displacement gives constant indentation strain. Thus, data from this type of measurement method are more easily analyzed and compared to traditional bulk stress relaxation data.However, because very fast initial force and displace ment rates are normally used in creep and stress relax-ation tests, respectively, the use of feedback combined with instrument limitations typically causes issues regarding how fast the force or displacement can be applied and then held constant without substantial over-shooting or undershooting, which can affect the quality particularly of the short-time data. An example of indentation stress relaxation data taken on a force-controlled system is shown in Fig. 4 to illustrate this problem.

<!-- 252 -->

<!-- Volume 108, Number 4, July-August 2003 -->

<!-- Journal of Research of the National Institute of Standards and Technology -->

<!-- 0.25 0.20 (mN) 0.15 Load 0.10 0.05 0.00 0 20 40 60 80 100 Time (s) -->
![](https://web-api.textin.com/ocr_image/external/581503a7f8e99d2a.jpg)

(a)

<!-- 120 90 Displacement (nm) 60 30 0 0 20 40 60 80 100 Time (s) -->
![](https://web-api.textin.com/ocr_image/external/373f645fd05cc41c.jpg)

(b)

<!-- 1.2 Contact Area(μ㎡) 0.9 0.6 0.3 0.0 0 20 40 60 80 100 Time (s) -->
![](https://web-api.textin.com/ocr_image/external/b09209653539d9b8.jpg)

(c)

Fig. 3. Force-time (a) and corresponding displacement-time (b) and contact area-time data(c)for an indentation creep test using a force-controlled system.

<!-- 253 -->

<!-- Volume 108, Number 4, July-August 2003 -->

<!-- Journal of Research of the National Institute of Standards and Technology -->

<!-- 250 200 Displacement (nm) 150 100 50 0 0 20 40 60 80 100 120 Time (s) -->
![](https://web-api.textin.com/ocr_image/external/dfe0d08f23c185f4.jpg)

(a)

<!-- 200 150 Load (μN) $Load(uN)$ 100 50 0 0 20 40 60 80 100 120 Time (s) -->
![](https://web-api.textin.com/ocr_image/external/822384562e4ba49f.jpg)

Fig.4. Displacement-time (a) and corresponding force-time (b) for an indentation stress-relaxation test using a force-controlled system and feedback to control displacement.

<!-- $MW$ $K_{f}$ $WW$ $\mathrm {K}_{\mathrm {s}}$ D S C mi $\mathbf {m}_{\mathrm {i}}$ -->
![](https://web-api.textin.com/ocr_image/external/1d07dd85aba6467d.jpg)

Fig. 5. Schematic illustration of a dynamic model for an instru-mented indentation system. $K_{\mathrm {f}}$ epresents the load-frame stiffness, $K_{\mathrm {s}}$ represents the stiffness of the springs, $D$  and $m_{i}$  represent the damping characteristics and mass, respectively, of the instru-ment, and $S$  and C represent the storage and loss components,re-spectively, of the mechanical impedance related to the tip-sample contact.

Recently, test methods have been used that combine dynamic oscillation with the quasi-static testing capa-bilities of instrumented indentation systems. A typical dynamic model of the indentation system represented in $Fig.$ 1 is shown schematically in 1Fig.5.When dynamic oscillation is applied, it is most often super-posed over a quasi-static force history using a small force or displacement amplitude and a frequency in the range of 1 Hz to 300 Hz [19,37].As will be discussed further in Sec. 2.3, the equations developed for the dynamic model are used to determine the contact stiff-ness throughout the force history, which in turn allows the contact area and sample modulus to be estimated throughout the force history. This technique is thus particularly useful for characterizing modulus as a function of depth, estimating changes in contact area during an indentation creep test (see Fig. 3c), and exploring the storage and loss responses of materials,for example. Additionally, the statistical sampling of indentation testing is dramatically improved over get ting one set of values for a given test from analysis of the unloading curve slope (see Sec. 2.3). Also, certain parameters related to the system dynamics will change dramatically at the onset of tip-sample contact, signifi cantly improving the ability to determine this point in the indentation data.

<!-- 254 -->

<!-- Volume 108, Number 4, July-August 2003 -->

<!-- Journal of Research of the National Institute of Standards and Technology -->

### 2.3 Analysis Techniques

The analysis of force-displacement curves produced by instrumented indentation systems is often based on work by Doerner and Nix [29] and Oliver and Pharr [28]. Their analyses were in turn based upon relation ships developed by Sneddon [38] for the penetration of a flat elastic half space by different probes with partic ular axisymmetric shapes (e.g., a flat-ended cylindrical punch, a paraboloid of revolution, and a cone). These elasticity-based analyses are normally applied to the unloading data of an indentation measurement, assum ing the unloading behavior of the material is character ized by elastic recovery only. In general, the relation ships between penetration depth, h, and force, P, during unloading can be represented in the form

$$P=\alpha (h-h_{f})^{m}\tag{2}$$

The parameter $α$  contains geometric constants, the sample elastic modulus, E, the sample Poisson's ratio, $V,$ , the indenter elastic modulus, $E_{\mathrm {i}},$  and the indenter Poisson's ratio, $V_{\mathrm {i}};$  the parameter $h_{\mathrm {f}}\text {is}$ the final unload ing depth; and m is a power law exponent that is relat ed to the geometry of the indenter (see Table 1). A non linear power law fit to the unloading data, where α, $h_{\mathrm {f}},$ and $m$  are fitting parameters, often yields a good estimate of the data, as does a smooth spline fit [20].However, previous research at NIST has shown that the practice of arbitrarily fitting portions of the unloading data can introduce bias into the calculations, and that data should be removed for curve fitting purposes only when the corresponding residual errors do not conform to the assumptions underlying the curve fitting methods [20]. Once an appropriate fit is obtained, a derivative, $dP/dh$ , applied at the maximum loading point $\left(h_{\max },\right.$ $\left.P_{\max }\right)$  should yield information about the state of contact at that point. This derivative is termed the contact stiff ness, S, and is given analytically by

$$S=2aE_{r}=\frac {2}{\sqrt {\pi }}E_{r}\sqrt {A}\tag{3}$$

Table 1. Theoretical values of parameters $m$  and $ε,$  both of which are related to the contact geometry, for three axisymmetric tip shapes [38], where $m$  is the power law exponent of Eq. (2) and $3$ is a factor used in determining the contact depth [see Eq. (6)].


| Tip geometry  | m  | ε |
| --- | --- | --- |
| Flat-ended cylindrical punch  | 1  | 1  |
| Paraboloid of revolution  | 1.5  | 0.75  |
| Cone  | 2  | $2(\pi -2)/\pi$ |


In this equation, the cross section of the indenter is assumed to be circular in relating the contact radius, $a,$ to the projected area of tip-sample contact, A. A small correction is sometimes applied for non-circular cross sections [26] and other corrections have been suggest ed [39]. The reduced modulus, $E_{\mathrm {r}}$ , accounts for elastic deformation of both the indenter and the sample and is given by

$$\frac {1}{E_{\mathrm {r}}}=\frac {\left(1-v^{2}\right)}{E}+\frac {\left(1-v_{\mathrm {i}}^{2}\right)}{E_{\mathrm {i}}}.\tag{4}$$

In Fig. 6, an indentation force-displacement curve is illustrated along with several important parameters used in the Oliver and Pharr analysis. The measured stiffness, $S^{*}$ , is the slope of the tangent line to the unloading curve at the maximum loading point $\left(P_{\max }\right)$ and is given by

$$S^{*}=\left(\frac {\mathrm {d}P}{\mathrm {\sim d}H}\right)_{P_{\max }}=am\left(h_{\max }-h_{\mathrm {f}}\right)^{m-1}.\tag{5}$$

<!-- $max$ $S^{*}$ $\mathbf {h}_{\mathrm {f}}longrightarrow$ $\mathbf {h}_{\max }$ -->
![](https://web-api.textin.com/ocr_image/external/0c78fa05d502b3ee.jpg)

$$h_{\max }=\text {maximumdisplacement}$$

$$\mathbf {h}_{\mathrm {f}}=\text {finaldepth}$$

Fig. 6. An indentation force-displacement curve in which several important parameters used in the Oliver and Pharr analysis are illustrated.

<!-- 255 -->

<!-- Volume 108, Number 4, July-August 2003 -->

<!-- Journal of Research of the National Institute of Standards and Technology -->

The parenthetic subscript denotes that the derivative is evaluated at the maximum loading point. Physically,the elastic recovery of the material is instantaneous upon unloading, so the true elastic response of the material can only be evaluated $at$ $t=0^{+}$ , where unload ing initiates at $t=0$ . When the displacement, $h,$  is the total measured displacement of the system, $S^{*}$  is the total system stiffness. After successful calibration of the load-frame compliance (see Sec. 2.4), the displace ment of the load frame is removed so that $h$  represents only the displacement of the tip into the sample, and $S^{*}=S.$  The contact depth, $h_{\mathrm {c}}$ , is related to the deforma tion behavior of the material and the shape of the indenter, as illustrated in Fig. 7, and is given by $h_{\mathrm {c}}=h_{\max }-h_{\mathrm {s}},$  where $h_{\mathrm {s}}$ is defined as the elastic displace ment, sometimes referred to as sink-in, of the surface at the contact perimeter. For each of three specific tip shapes (flat-ended punch, paraboloid of revolution, and cone), $h_{\mathrm {s}}=\varepsilon P_{\max }/S$ where $3$  is a function of the partic ular tip geometry, as summarized in Table 1. Thus, $h_{\mathrm {c}}\text {is}$ given by

$$h_{\mathrm {c}}=h-\frac {\varepsilon P}{S}.\tag{6}$$

For the purposes of the Oliver-Pharr analysis, $h=h_{\max }$ and $P=P_{\max }$  in Eq. (6). Also, $h_{\mathrm {c}}<h_{\max }$  such that this equation is not valid when pile-up occurs, i.e., when material is forced up along the sides of the indentation tip. As indicated in Table 1, the choice of $3$  should be related to the value of $m$  determined from the curve fitting [40]. However, a value of 0.75, corresponding to $m=1.5,$  is used almost exclusively for spherical,conical, and pyramidal indenters, regardless of the value of $m$ . Once $h_{\mathrm {c}}$ has been determined, the tip shape function, $A\left(h_{\mathrm {c}}\right)$  (see Sec. 2.4) is used to calculate the contact area, such that the sample modulus, E, can be determined from Eq. (3) and Eq. (4), given a reasonable estimate of $V$ 

Despite the use of feedback in some cases, the dynamic model of $Fig.$  5 is normally treated as a simple damped harmonic oscillator under conditions of an applied harmonic force, $P=P_{0}$ · exp (iω t ), with a resulting harmonic displacement, $h=h_{0}$ · exp (iω t – φ),where $ω$ i s the applied oscillation frequency and $Φ$ i s the phase angle by which the displacement lags the force.The equations of motion developed for this model (with sample contact) can be solved to yield an equation for the contact stiffness, S, that is a function of previously calibrated instrument parameters (i.e., $K_{\mathrm {f}},$ $K_{\mathrm {s}}$ , and $m_{\mathrm {i}}$ ), $ω$  , $ø,$  the harmonic force amplitude, $P_{0},$  and the har monic displacement amplitude, $h_{0}:$ 

$$S=\left[\frac {1}{\frac {P_{0}}{h_{0}}\cos \phi -\left(K_{\mathrm {s}}-m\omega ^{2}\right)}-\frac {1}{K_{\mathrm {f}}}\right]\tag{7}$$

Also, the damping factor, $C$ , attributed to the tip sample contact is given by:

$$C\omega =\frac {P_{0}}{h_{0}}\sin \phi -D\omega .\tag{8}$$

Superposing oscillation during quasi-static loading thus allows $S$  to be estimated as a function of depth through out the loading segment. Equation (6) can then be used to monitor $h_{\mathrm {c}}$  continuously, knowledge of the tip shape yields an estimate of A continuously, and thus E can be measured continuously using Eq. (3) and Eq. (4).Because these relationships can be built into the soft ware, the use of dynamic oscillation superposed over the loading history simplifies the analysis procedures greatly. Additionally, the amount of data associated with one such experiment is equivalent to many experiments in which only quasi-static loading is used,allowing more robust statistical analysis to be performed. 

<!-- $\mathbf {P}_{\max }$ $\mathbf {h}_{\mathrm {s}}$ $\mathbf {h}_{\mathrm {c}}$ $\mathbf {h}_{\max }$ -->
![](https://web-api.textin.com/ocr_image/external/125c10bc975c1f05.jpg)

Fig. 7. Illustration of the indentation geometry at maximum force for an ideal conical indenter.

<!-- 256 -->

<!-- Volume 108, Number 4, July-August 2003 -->

<!-- Journal of Research of the National Institute of Standards and Technology -->

### 2.4 Calibration Issues

Very little discussion of calibration issues related to instrumented indentation systems can be found in the open literature. As with most measurement systems,calibration is essential for limiting uncertainties and achieving reproducible and repeatable measurements.The most fundamental measures made by these systems are of force and displacement. Many instruments are capable of operating at forces less than 1 mN, and in some literature, force resolutions of $1μN$  or less are claimed. Currently, however, force is typically calibrat ed by hanging standard weights on the force measure ment device, and deadweight force standards are only available for calibrating forces down to approximately $10N$ . Current NIST research aimed at improving available force standards at the micro-Newton and nano-Newton levels is discussed in Sec. 3.1.

Calibration of displacement can be done using sever al methods, such as by using separately calibrated transducers or by using interferometric methods.Again, however, many instruments are capable of oper ating with displacements and displacement resolutions significantly smaller than the resolution of the calibra tion methods. Further, force and displacement measure ments are typically coupled in instrumented indentation systems through the support springs. Thus for force driven systems, for example, calibrating displacement is equivalent to calibrating the spring stiffness or spring constant, which links the raw displacement of the system to the raw force. Assuming the spring response is linear, displacements can then be determined with uncertainties related to uncertainties in the force calibration and the spring constant.

The calibration of load-frame compliance, C $C^{*}$  is difficult and can have a significant amount of uncer tainty, and even qualitative assessment of indentation behavior depends critically on the accuracy of this cal ibration step, especially from laboratory to laboratory and instrument to instrument. Prior to calibration (i.e., $C_{\mathrm {lf}}$ is unknown), the measured displacement, $h_{\text {total}},$  is a combination of displacement of the load frame, $h_{\mathrm {lf}},$  and displacement of the sample, $h_{\mathrm {sp}}$ . Treating the system as two springs (the load frame and the sample) in series under a given force, $P$ ,

$$h_{total}=h_{lf}+h_{sp}\tag{9}$$

Dividing both sides by $P$ ,

$$C_{\mathrm {total}}=C_{\mathrm {lf}}+C_{\mathrm {sp}}=C_{\mathrm {lf}}+\frac {\sqrt {\pi }}{2E_{\mathrm {r}}}\frac {1}{\sqrt {A}}.\tag{10}$$

The total compliance is related to total stiffness, $S^{*},$  by $C_{\text {total}}=1/S^{*}$ and the sample compliance is related to the contact stiffness, S, by $C_{\mathrm {sp}}=1/S.$  A number of possible methods exist for determining $C_{\mathrm {lf}}$  using reference samples that are homogeneous and isotropic and for which both E and $V$  are known. Typically, a series of indentation measurements are made on a single refer ence sample or multiple reference samples. Oliver and Pharr [28] suggested using an iterative technique to calibrate both the load-frame compliance and the tip shape with one set of data from a single reference sample, as both $C_{\mathrm {tf}}$ and A are, in general, unknowns in Eq. (10). While this method has the advantage of not requiring an independent measurement of the area of each indent, its use has been limited, perhaps because it is mathematically and time intensive. 

For the load-frame compliance calibration, the choice of reference sample(s) should be made with an objective of maximizing contact stiffness (minimizing $\left.C_{\mathrm {sp}}\right)$  so that $C_{\text {total}}$  is dominated by $C_{\mathrm {lf}}$  Thus, relatively large indentation forces and depths are normally applied to a reference material that either has a high modulus or exhibits significant plastic deformation,i.e., a sample that has a high ratio of E/H. Use of a high ly plastic material such as aluminum, for which the pro jected area should be similar to the contact area, A, at maximum force, can be combined with high resolution imaging techniques, such as electron microscopy or atomic force microscopy (AFM) to determine $C_{\mathrm {lf}}$  from a plot of $C_{\text {total}}$  as a function of $1/\sqrt {A}$ . Alternatively, an additional assumption that H is constant with depth can allow $C_{\mathrm {lf}}$ to be determined from a plot of $C_{\text {total}}$ as a function of $1/\sqrt {P_{\max }}$ . In this case, aluminum is often replaced by fused silica, because oxide formation on aluminum can create variations in both E and $H$  with penetration depth. For all of these methods, the calcu lation of $C_{\mathrm {lf}}$ based on Eq. (10) requires a large extrapo lation of the experimental data. Futher, the $x$ -variable has significant uncertainty, which is a violation of the assumptions of least squares regression, leading to the creation of bias in the least squares estimate of $C_{\mathrm {lf}}$ such that the estimated value is lower than the actual value.These issues, along with other sources of uncertainty,can result in a large amount of uncertainty associated with the load-frame compliance, which will then affect all subsequent calculations [20, 41]. A review of these uncertainties along with a newly proposed method of load-frame compliance calibration that is independent of reference materials can be found in Ref. [42].

For the tip shape calibration, the series of indents applied to a reference material typically covers a larger 

<!-- 257 -->

<!-- Volume 108, Number 4, July-August 2003 -->

<!-- Journal of Research of the National Institute of Standards and Technology -->

$$Fig.\quad a,\quad h_{\mathrm {c}}\quad h_{\max }\quad P_{\max }\quad h_{\mathrm {c}},\quad A(h_{c}),\quad \mathrm {Nc}\quad A\quad h_{\mathrm {c}}$$

$$A\left(h_{\mathrm {c}}\right)=B_{0}h_{\mathrm {c}}^{2}+B_{1}h_{\mathrm {c}}+B_{2}h_{\mathrm {c}}^{1/2}+\cdots .\tag{11}$$

In this equation, $B_{0},B_{1},\cdots ,$ $B_{\mathrm {n}}$ are constant coefficients determined by the curve fit. For example, for a Berkovich indentation tip, Oliver and Pharr [28] sug gested using up to nine terms $(n=8)$  with $B_{0}=24.5,$ where the area function of a perfect Berkovich tip is $A(h_{c})=24.5$ $h_{\mathrm {c}}{}^{2}.$  The additional terms attempt to account for deviations from ideal geometry, such as blunting of the tip.

The use of dynamic oscillation can significantly enhance the calibrations of load-frame compliance and tip shape, particularly with regard to improving the statistical sampling and reducing the amount of time required. For example, multiple deep indentations on a reference sample using oscillation superposed over the loading segment of each test yields multiple sets of modulus values as a function of penetration depth that can then be averaged and used either to check load frame compliance or tip shape calibration. In fact, both can at least be checked with the same data if the refer ence sample (e.g., fused silica glass) has both a modu lus and a hardness that is independent of depth. Thus,the E vs h data can be used to check tip shape calibra tion, and for a proper load-frame compliance cali bration, the ratio of force to contact stiffness squared $\left(\mathrm {P}/S^{2}\right),$  which is proportional to $H/E_{\mathrm {r}}$ , should be inde pendent of depth regardless of the tip shape function.Additionally, the improved capabilities for detecting the surface using dynamic oscillation reduce the uncer tainties in the calibrations related to the choice of the initial point of contact.

Dynamic calibrations of the system are typically made with respect to the dynamic model shown in Fig. 5 [37]. System calibrations are then performed by measuring the dynamic response with no sample involved. The load-frame stiffness, $K_{\mathrm {f}},$  is normally assumed to be infinite (i.e., load-frame compliance is zero). By monitoring amplitude and phase shift, the equations derived for the model can be used to deter mine the resonance frequency of the system, the system damping coefficient, $D$ , the mass, $m_{\mathrm {i}}$ , and the spring constant, K $F_{浮}$ As discussed previously, the spring con stant, which is typically independent of frequency over a wide frequency range, can be determined from raw force as a function of raw displacement, and the system mass can be determined from the displacement at zero force. Also, $D$  is often assumed to be independent of frequency, which is not necessarily true [43]. 

## 3.Research Efforts at NIST

### 3.1 Improving Force Calibration

A desire for accurate, traceable, small force measure ment is emerging within the International Organization for Standardization (ISO) task groups and ASTM International technical committees that work on instru mented indentation standards [44]. However, no meth ods for establishing force measurement traceability at these levels are currently available. A research effort has recently been developed at NIST (Microforce Realization Competence) with the purpose of creating a facility and instruments capable of providing a viable primary force standard below 1 $0^{-5}\mathrm {\sim N}$ , and with the goal of realizing force in this range at a relative uncertainty of parts in $10^{4}$  This new project complements a body of existing work at NIST to develop standards and meth ods for the instrumented indentation community that together provide a metrological basis for manufacturers seeking traceable characterization of, for example, thin film mechanical properties.

The most common approach to force realization is a calibrated mass in a known gravitational field or dead weight force, which is universally accepted as the primary standard of force. The smallest calibrated mass available from NIST is 1 mg (approximately a $10N$  deadweight force) having a relative uncertainty of about $10^{-4}$ . In principle, smaller masses could be calibrated, but they would be difficult to handle.Also, the relative uncertainty tends to increase in verse proportion to the decrease in mass [45], potential ly resulting in uncertainties that are of similar magni tude to deadweight forces in the range of nano Newtons.

<!-- 258 -->

<!-- Volume 108, Number 4, July-August 2003 -->

<!-- Journal of Research of the National Institute of Standards and Technology -->

Alternatively, forces in this range can be realized using the electrical units defined in the International System of Units (SI) and linked to the Josephson and quantized Hall effects in combination with the SI unit of length. This realization can be done using electromagnetic forces (e.g., the NIST Watt Balance Experiment [46]) or using electrostatic forces [47]. In this research, the latter was chosen because the required metrology is somewhat simpler to execute, and the forces generated, although generally less than those feasible electromagnetically, are appropriate for the force range of interest. Also, electrostatic force genera tion is common in micro-electromechanical systems (MEMS), and the ability to calibrate such forces from electrical and length measurements could prove beneficial.

The mechanical work required to change either the overlap or the separation of two electrodes in a one dimensional capacitor while maintaining constant voltage is

$$\mathrm {d}W=F·\mathrm {\sim d}z=\frac {1}{2}V^{2}\mathrm {\sim d}C\tag{12}$$

In this equation, dW is the change in energy (mechani cal work), F is the force, $\mathrm {d}z$  is the change in the overlap or separation of the electrodes, V is the electric poten tial across the capacitor, and dC is the change in capac itance. Thus, force can be realized from electrical units by measuring V and the capacitance gradient, $dC/dz$  or:

$$F=\frac {1}{2}V^{2}\frac {\mathrm {\sim d}C}{\mathrm {\sim d}z}\tag{13}$$

This idealized, one-dimensional approximation does not account for multi-dimensionality, external fields or stray electrical charges likely to be present in the actual physical system. The goal then is to develop a system that reproduces this idealization as closely as possible by using effective constraints on the geometry,shielding, and suspension of the resulting electrodes.Additionally, validation of this electrostatic force realization through comparison to deadweight forces will be advantageous, at least in the higher force range where the uncertainty that can be achieved mechanical ly is still competitive. In consideration of these factors,a force generator was designed to operate along the vertical axis as part of an electromechanical null balance shown in Fig. 8. Recent results with this instru ment [48, 49], referred to as the NIST Electrostatic Force Balance or EFB, demonstrated a relative

<!-- $\mathbf {a}_{1}$ $a_{2}$ -->
![](https://web-api.textin.com/ocr_image/external/dcd6edde007709ba.jpg)

Fig. 8. The prototype electrostatic force balance. Inner cylindrical electrode of 15 mm dia. is suspended from a compound parallelogram leaf spring made of $50μm$  thick CuBe producing a single axis spring of stiffness 13.4 N/m. Deflections are measured using a double-pass Michelson interferometer and nulled using a feedback servo to apply voltage to the outer cylinder. Electrode gap is nominally 0.5 mm and overlap is nominally 5 mm.

<!-- 259 -->

<!-- Volume 108, Number 4, July-August 2003 -->

<!-- Journal of Research of the National Institute of Standards and Technology -->

standard uncertainty of about $10^{-4}\mathrm {in}$ the comparison of gravitational and electrostatic forces ranging between $10N$  and $100μN$ . This resuult indicates that the elec-trostatic force can be constrained and measured in a fashion traceable to the SI and with accuracy sufficient to warrant consideration as a primary standard of force in this regime.

### 3.2 Improving Tip Shape Calibration

A number of recent efforts have been made to improve tip shape calibration for instrumented indenta-tion [41,50-55].These efforts have included material-independent methods of tip shape calibration using AFM [41,50-52] and alternative procedures using indentation of reference materials [53-55]. Recent research at NIST has focused on methods in which the indenter tip is scanned with an AFM probe to yield direct information regarding the three-dimensional tip shape [53,56]. Because an AFM image is a combina-tion of the AFM probe geometry and the geometry of the sample surface, AFM imaging of indentation tips was combined with AFM imaging of a tip characteriz-er surface, which allows for an estimation of the three-dimensional shape of the AFM probe using the method of blind reconstruction [57, 58].This estimation of the AFM probe geometry can then be eroded from the image of the indentation tip to remove dilation and other artifacts created by the AFM probe, as described in detail in Ref. [50].

In principle, because the AFM probe acts to produce image geometry that is dilated from the true surface geometry, the area function (cross-section area as a function of distance from the apex) of the indentation tip determined from an AFM image is an outer bound on the true area function. Also, because the AFM probe geometry estimated using blind reconstruction is an outer bound on the true probe geometry, eroding this estimated geometry from an AFM image of the inden-tation tip produces a lower bound on the tip area func-tion.In reality,however,other artifacts or uncertainties associated with the AFM image of the indentation tip will affect the results, particularly for open-loop AFM systems. This effect is shown in Fig. 9 in which area functions are compared for consecutive images of the same size and of different sizes. For close-loop AFM systems, particularly those with calibrated vertical motion such as the NIST Calibrated-AFM [59], the images produced of the tip shapes can have much less uncertainty.

Comparisons of tip shape data generated from AFM imaging to that determined from indentation of fused silica (for example, see Fig. 9) revealed a potential problem with determining tip shape area functions using indentation of reference samples. Differences between AFM-generated data and indentation data were most significant at small depths and increased as a function of the indenter tip radius. Values of cross-section area from indentation data were always less than that from AFM data. This result appears to at least

<!-- 3.0 $16umx16$  um image 1 original $16mx16μmimage$  1 $\left(μ\mathrm {m}^{2}\right)$ ㎡ 2.5 $16\text {um}\times 16$  um image 1 eroded original and eroded $3um\times 3um$ x image original 2.0 $3umx3$ um image eroded Cross-section area  1.5 Fused silica indentation 1.0 $3μmx3μm$ image original and eroded 0.5 0.0 0 50 100 150 200 250 300 Distance from apex (nm) -->
![](https://web-api.textin.com/ocr_image/external/6080a1bebaee0aad.jpg)

**Fig.9.** Plot of the estimated cross-section area of a Berkovich indentation tip as a function of the distance from the apex. Data are shown for two $3\mu \mathrm {\sim m}\times 3\mu \mathrm {\sim m}$  images, one $16\mu \mathrm {\sim m}\times 16\mu \mathrm {\sim m}$ image, each of the three AFM images after eroding away the estimated AFM probe geometry, and indentation of fused silica. Only the first 300 nm of data are shown to emphasize differences.

<!-- 260 -->

<!-- Volume 108, Number 4, July-August 2003 -->

<!-- Journal of **Research** **of** **the** National Institute of Standards and Technology -->

partially explain results in which indentation modulus $(E\propto S/\sqrt {A})$  is significantly higher than modulus values measured with other techniques, particularly for poly-mers where S is relatively small for a given contact depth such that errors in A have a larger effect and low values of A will result in artificially high modulus values. Also, this results could also explain the many reports of indentation hardness $(H=P/A)$ values being larger at small depths compared to large depths, often referred to as the indentation size effect. Thus,the uncertainties associated with tip shape calibration using indentation of reference samples are expected to be significantly larger than those associated with AFM-generated tip shape information in many cases. In fact,this independent assessment of the tip shape via AFM can then be used to help calibrate load-frame compliance using a known tip area function.

### 3.3 Applications of Instrumented Indentation to Polymeric Materials

Instrumented indentation is increasingly being used to probe the mechanical response of polymeric and biological materials. These types of materials behave in a viscoelastic fashion, i.e., they display mechanical properties intermediate between those of an elastic solid and a viscous fluid, as shown in Fig. 2 and Fig. 3by the changes in displacement under constant force conditions and in Fig. 4 by the changes in force under constant displacement conditions. The mechanical behavior is thus dependent on the test conditions,including amount of strain, strain rate, and temperature.Often in instrumented indentation,however, properties are measured using loading histories developed for elastic and elasto-plastic materials, the properties of which are not particularly time dependent, and the analysis of the indentation response is typically based on elasticity theory. In studies in which attempts have been made to characterize viscoelastic behavior, limit-ing and sometimes invalid assumptions have been made, and linear viscoelasticity has been applied despite the intense strains local to the indenter tip that would appear to violate the linear viscoelasticity premise of infinitesimal strains [60].

Another issue that can add significant uncertainty to indentation measurements of polymers is the ability to detect the surface.Polymers and other organic materi-als are typically much more compliant compared to the metallic and ceramic types of materials to which instrumented indentation mainly has been applied, with modulus values ranging from a few GPa for common glassy polymers to a few MPa or lower for rubbery polymers and many biological materials. As mentioned previously, the use of small dynamic oscillations has improved sensitivity to surface contact. However,as the compliance of the material increases,depending on the particular indentation system, the changes used to define surface contact become of similar magnitude to the noise level. In some cases, manual selection of the contact point in the raw test data after the test is com-pleted can be used to correct any automated selection by the system or to check the sensitivity of the calcula-tions to this choice. However, in other cases, the system selection of the contact point afTects the start of the test and thus the start of any feedback that might be used to control the test flow. In such cases,the approach velocity of the probe can be an important factor,as the initial part of the indentation data prior to feedback control will be based on this approach velocity. For example,the indentation strain rate, $\dot {\varepsilon }_{i}$ ,as estimated by the ratio $\dot {P}/P$ , and modulus areplotted in Fig.10as functions of penetration depth for a polystyrene material. The feedback used to keep $\dot {P}/P$  constant does not take effect until the probe is over 100 nm into the material. Although other factors contribute to significant uncertainty at small depths, the large changes in indentation strain rate could also have affected the resulting modulus values.

In recent research at NIST, analyses by Ting [61]that are based on contact between a rigid indenter and a linear viscoelastic material were revisited and used to determine under what conditions, if any, instrumented indentation can be used to measure linear viscoelastic behavior for a number of different polymers [58]. For example,the creep compliance, $J(t)$ , of a linear vis-coelastic material subject to a constant indentation or creep force, $P_{0},$ using a conical tip of semi-apical angle, $\theta$ , is proportional to the change in contact area with time, $A(t)$  [61]:

$$J(t)\propto \frac {A(t)}{P_{0}\tan \theta }\tag{14}$$

Note that in this equation, (1/tan $\theta$  is related to a nom-inal indentation strain and $P/A$  is related to a nominal indentation stress, such that $J(t)$  is proportional to an indentation strain over an indentation stress. Similar equations can be determined for other tip geometries,and equations can be derived relating stress relaxation modulus to the change in force with time during a constant displacement indentation test for various tip geometries.

<!-- 261 -->

<!-- Volume 108, Number 4, July-August 2003 -->

<!-- Journal of Research of the National Institute of Standards and Technology -->

<!-- 0.10 0.08 Strain Rate (1/s) 0.06 0.04 0.02 0.00 0 200 400 600 800 1000 Displacement into Surface (nm) -->
![](https://web-api.textin.com/ocr_image/external/56a7d48940239eb8.jpg)

(a)

<!-- 10 8 Modulus (GPa) 6 Lower indentation strain rate 4 2 Higher indentation strain rate 0 0 200 400 600 800 1000 Displacement into Surface(nm) -->
![](https://web-api.textin.com/ocr_image/external/94d446306334ea10.jpg)

(b)

**Fig.10.** Plots of indentation strain rate, $\dot {\varepsilon }_{i}$ , estimated by the ratio $\dot {P}/P$  (a) and indentation modulus (b) as a function of depth, $h$ , for a constant $\dot {P}/P$  test using a Berkovich indentation tip to pene-trate a polystyrene sample. Date for one test each at two ddifferent rates are shown. Differences in the modulus data are estimated to be within the measurement uncertainty.

In these studies, constant force indentation creep tests and constant penetration depth stress relaxation tests were used, and the results were compared to traditional solid rheological measurements [56]. An example of indentation creep compliance measure-ments for an epoxy material using a rounded conical tip (manufacturer-determined tip radius of $10μm$  is shown in Fig. 11 [proportionality constant of 1.0assumed in Eq.(14)]. The dependence of creep compli-ance on the creep force, as shown by the displacement between the curves, is an indication of nonlinear behav-ior, and in fact, the indentation creep behavior of a number of polymeric materials was dominated by nonlinear viscoelastic behavior. Additionally, probe tip size and shape were altered to produce different nomi-nal indentation strains, $\varepsilon _{i}$ ,and the measured respons-es appeared to be correlated with $\varepsilon _{i}$ i. Analyses and protocols are currently being explored for relating instrumented indentation data to viscoelasticity and ultimately to stress-strain behavior of polymers using various indentation tips.

<!-- 262 -->

<!-- Volume 108, Number 4, July-August 2003 -->

<!-- Journal of Research of the National Institute of Standards and Technology -->

<!-- -8.6 1.00 1.25 1.50 1.75 2.00 2.25 -8.7 20mN -8.8 $\left(\mathrm {Pa}^{-1}\right.$ 10mN log J(t)) 5 mN -8.9 ←2.5mN 1 mN 6- 0.5mN -9.1 0.2mN -9.2 log t(s) -->
![](https://web-api.textin.com/ocr_image/external/0adb3b09a792225d.jpg)

Fig. 11. Log-log plot of creep compliance, $J(t)$  as a function of time, $t,$  for an indentation creep experiment on epoxy using a rounded conical tip (manufacturer-determined tip radius of $10μm$  . Error bars shown represent an estimated standard deviation $(k=1).$ 

In addition to the quasi-static studies, measurements of viscoelastic behavior using dynamic indentation techniques are also being explored. From the dynamic model of the indentation system (see Fig.5), equations have been derived for determining the storage modulus, $E^{\prime }$ ,and loss modulus, $E^{\prime \prime }$ of a viscoelastic material [18,19,37]:

$$E^{\prime }=\frac {\sqrt {\pi }}{2\sqrt {A}}S\tag{15}$$

$$E^{\prime \prime }=\frac {\sqrt {\pi }}{2\sqrt {A}}C\omega .\tag{16}$$

Thus, $E^{\prime }$  is assumed to be directly related to the storage portion, S, of the mechanical impedance of the tip-sample contact in the dynamic model (see Fig.5),and $E^{\prime \prime }$ is assumed to be directly related to the loss portion, $Cω$ , of the mechanical impedance of the tip-sample contact. However, this assumption was found to have significant limitations with regard to lossy polymers [43]. At NIST, new analysis methods are currently being developed for analyzing the dynamic mechanical response to indentation of viscoelastic materials,in particular to determine under what conditions Eq.(15)and Eq. (16) hold. A number of different polymers are being studied, the results of which are being compared to traditional dynamic mechanical measurements.

## 4. Summary

As instrumented indentation techniques gain wider use and application, standardization efforts increase in importance. NIST personnel are involved in the ASTM Task Group E28.06.11 developing ASTM standard practices and standard test methods for instrumented indentation testing and have participated in internation-al round robin testing. Deficiencies in current practices include the need to use reference materials for calibra-tions of load-frame compliance and tip shape, the lack of traceable force calibration below $10μN$ , and the lack of uncertainty budget analysis related to measurement techniques and analyses. Current research at NIST is focused on independent methods for tipshape calibra-tion, traceable calibration methodsfor micro-Newton and nano-Newton level forces, and applications to viscoelastic materials such as polymeric and biological materials.

### Acknowledgements

The author gratefully acknowledges the contribu-tions by Doug Smith and his colleagues involved in the NIST Microforce Realization and Measurement project. Additionally, the author acknowledges many fruitful collaborations, including those with Chris White, John Villarrubia, and Will Guthrie of NIST,Xiaohong Gu of the University of Missouri-Kansas City, Vincent Jardret at MTS Systems Corp., and Greg Meyers at the Dow Chemical Company, as well as helpful discussions with Don Hunston and Patty McGuiggan of NIST, Greg McKenna of Texas Tech University, and Al Crosby of the University of Massachusetts at Amherst.

<!-- 263 -->

<!-- Volume 108, Number 4, July-August 2003 -->

<!-- Journal of Research of the National Institute of Standards and Technology -->

## 5.References

[1] G. E. Dieter, Mechanical Metallurgy, McGraw Hill, New York (1986).

[2] W. D. Nix and H. Gao, Indentation size effects in crystalline materials: A law for strain gradient plasticity, J. Mech. Phys.Solids 46 (3), 411-425 (1998).

[3] Q. Ma and D. R. Clarke, Size-dependent hardness of silver sin gle-crystals, J. Mater. Res. 10 (4), 853-863 (1995).

[4] S. G. Corcoran, R. J. Colton, E. T. Lilleodden, and W. W.Gerberich, Anomalous plastic deformation at surfaces:Nanoindentation of gold single crystals, Phys. Rev. B 55 (24),16057-16060 (1997).

[5] D. R. Clarke and R. Tandon, Factors affecting the fracture resistance of silicon-nitride ceramics, Mater. Sci. Eng. A 195(1-2), 207-214 (1995).

[6] G. M. Pharr, Measurement of mechanical properties by ultra low load indentation, Mater. Sci. Eng. A 253 (1-2), 151-159(1998).

[7] E. T. Lilleodden, J. A. Zimmerman, S. M. Foiles, and W. D.Nix, An experimental and computational study of the elastic plastic transition in thin films, in Dislocations and Deformation Mechanics in Thin Films and Small Structures, Vol. 673,O. Kraft, K. Schwarz, S. P. Baker, B. Freund, and R. Hull, eds.,Materials Research Society, Pittsburgh, PA (2001) pp. 131-136.

[8] N. Huber, W. D. Nix, and H. Gao, Identification of elastic plastic material parameters from pyramidal indentation of thin films, Proc. Roy. Soc. London A 458 (2023), 1593-1620(2002).

[9] R. Saha and W. D. Nix, Effects of the substrate on the determi nation of thin film mechanical properties by nanoindentation,Acta Mater. 50 (1), 23-38 (2002).

[10] T. Y. Tsui and G. M. Pharr, Substrate effects on nanoindentation mechanical property measurement of soft films on hard sub strates, J. Mater. Res. 14 (1), 292-301 (1999).

[11] Z. Fan, J. G. Swadener, J. Y. Rho, M. E. Roy, and G. M. Pharr,Anisotropic properties of human tibial cortical bone as meas ured by nanoindentation, J. Orthopaed. Res. 20 (4), 806-810(2002).

[12] J. G. Swadener, B. Taljat, and G. M. Pharr, Measurement of residual stress by load and depth sensing indentation with spherical indenters, J. Mater. Res. 16 (7), 2091-2102 (2001). 

[13] S. A. S. Asif and J. B. Pethica, Nano-scale indentation creep testing at non-ambient temperature, J. Adhesion 67 (1-4), 153165 (1998).

[14] S. A. S. Asif and J. B. Pethica, Nanoindentation creep of single crystal tungsten and gallium arsenide, Phil. Mag. A 76 (6),1105-1118 (1997).

[15] B. N. Lucas and W. C. Oliver, Indentation power-law creep of high-purity indium, Metall. Mater. Trans. A 30 (3), 601-610(1999).

[16] B. J. Briscoe, L. Fiori, and E. Pelillo, Nano-indentation of polymeric surfaces, J. Phys. D—Appl. Phys. 31 (19), 23952405 (1998).

[17] L. Cheng, X. Xia, W. Yu, L. E. Scriven, and W. W. Gerberich,Flat-punch indentation of viscoelastic material, J. Poly. Sci.B—Poly. Phys. 38 (1), 10-22 (2000).

[18] J. L. Loubet, W. C. Oliver, and B. N. Lucas, Measurement of the loss tangent of low-density polyethylene with a nanoinden tation technique, J. Mater. Res. 15 (5), 1195-1198 (2000).

[19] S. A. S. Asif and J. B. Pethica, Nano-scale viscoelastic proper ties of polymer materials, in Thin-Films-Stresses and Mechanical Properties VII, Vol. 505, R. C. Cammarata, M. A.Nastasi, E. P. Busso, and W. C. Oliver, eds., Materials Research Society, Pittsburgh, PA (1998) pp. 103-108. 

[20] M. R. VanLandingham, J. S. Villarrubia, W. F. Guthrie, and G. F. Meyers, Nanoindentation of polymers—An overview, in Macromolecular Symposia, Vol. 167, Advances in Scanning Probe Microscopy of Polymers, V. V. Tsukruk and N. D.Spencer, eds., Wiley-VCH Verlag GmbH, Weinheim, Germany (2001) 15-43.

[21] S. Shimizu, T. Yanagimoto, and M. Sakai, Pyramidal indenta tion load-depth curve of viscoelastic materials, J. Mater. Res.14 (10), 4075-4086 (1999).

[22] M. L. Oyen and R. F. Cook, Load-displacement behavior during sharp indentation of viscous-elastic-plastic materials,J. Mater. Res. 18 (1), 139-150 (2003). 

[23] N. X. Randall and R. Consiglio, Nanoscratch tester for thin film mechanical properties characterization, Rev. Sci. Instrum. 71(7), 2796-2799 (2000).

[24] V. Jardret, B. N. Lucas, W. C. Oliver, and A. C. Ramamurthy,Scratch durability of automotive clear coatings: A quantitative,reliable and robust methodology, J. Coating Technol. 72 (907),79-88 (2000).

[25] X. D. Li and B. Bhushan, Micro/nanomechanical and tribo logical studies of bulk and thin-film materials used in magnet ic recording heads, Thin Solid Films 398, 313-319 (2001).

[26] M. Dao, N. Chollacoop, K. J. Van Vliet, T. A. Venkatesh, and S. Suresh, Computational modeling of the forward and reverse problems in instrumented sharp indentation, Acta Mater. 49(19), 3899-3918 (2001).

[27] Y. T. Cheng, Z. Y. Li, and C. M. Cheng, Scaling relationships for indentation measurements, Philos. Mag. A 82 (10), 18211829 (2002).

[28] W. C. Oliver and G. M. Pharr, An improved technique for deter mining hardness and elastic modulus using load and displace ment sensing indentation measurements, J. Mater. Res. 7 (6),1564-1583 (1992).

[29] M. F. Doerner and W. D. Nix, A method for interpreting the data from depth-sensing indentation instruments, J. Mater. Res. 1(4), 601-609 (1986).

[30] B. Bhushan, A. V. Kulkarni, W. Bonin, and J. T. Wyrobek,Nanoindentation and picoindentation measurements using a capacitive transducer system in atomic force microscopy, Phil.Mag. A 74 (5), 1117-1128 (1996).

[31] D. Newey, M. A. Wilkins, and H. M. Pollock, An ultra-low-load penetration hardness tester, J. Phys. E–Sci. Instrum. 15 (1),119-122 (1982).

[32] T. J. Bell, A. Bendeli, J. S. Field, M. V. Swain, and E. G.Thwaite, The determination of surface plastic and elastic prop erties by ultra micro-indentation, Metrologia 28 (6), 463-469(1992).

[33] J. L. Loubet, J. M. Georges, and G. Meille, Vickers Indentation Curves of Elasto-Plastic Materials, in ASTM STP 889,Microindentation Techniques in Materials Science and Engineering, P. J. Blau and B. R. Lawn, eds., ASTM International, West Conshohoken, PA (1986) pp. 72-89.

<!-- 264 -->

<!-- Volume 108, Number 4, July-August 2003 -->

<!-- Journal of Research of the National Institute of Standards and Technology -->

[34] W. C. Oliver, R. Hutchings, and J. B. Pethica, Measurement of hardness at indentation depths as low as 20 nanometers, in ASTM STP 889, Microindentation Techniques in Materials Science and Engineering, P. J. Blau and B. R. Lawn, eds.,ASTM International, West Conshohoken, PA (1986) pp. 90-108.

[35] S. A. Joyce and J. E. Houston, A new force sensor incorporat ing force-feedback control for interfacial force microscopy,Rev. Sci. Instrum. 62 (3), 710-715 (1991).

[36] B. N. Lucas, W. C. Oliver, G. M. Pharr, and J. L. Loubet, Time dependent deformation during indentation testing, in Thin Films: Stresses and Mechanical Properties VI, Vol. 436, W. W.Gerberich, H. Gao, J-E. Sundgren, and S. P. Baker, eds.,Materials Research Society, Pittsburgh, PA (1997) pp. 233-238.

[37] S. A. S. Asif, K. J. Wahl, and R. J. Colton, Nanoindentation and contact stiffness measurement using force modulation with a capacitive load-displacement transducer, Rev. Sci. Instrum. 70(5), 2408-2413 (1999).

[38] I. N. Sneddon, The relationship between load and penetration in the axisymmetric Boussinesq problem for a punch of arbitrary profile, Int. J. Engng. Sci. 3, 47-57 (1965).

[39] J. C. Hay, A. Bolshakov, and G. M. Pharr, A critical examina tion of the fundamental relations used in the analysis of nanoin dentation data, J. Mater. Res. 14 (6), 2296-2305 (1999).

[40] G. M. Pharr and A. Bolshakov, Understanding nanoindentation unloading curves, J. Mater. Res. 17 (10), 2660-2671 (2002).

[41] N. M. Jennett and J. Meneve, Depth sensing indentation of thin hard films: A study of modulus measurement sensitivity to indentation parameters, in Fundamentals of Nanoindentation and Nanotribology, Vol. 522, N. R. Moody, W. W. Gerberich,N. Burnham, and S. P. Baker, eds., Materials Research Society,Pittsburgh, PA (1998) pp. 239-244. 

[42] K. J. Van Vliet, L. Prchlik, and J. F. Smith, Direct measurement of indentation frame compliance, J. Mater. Res., submitted (2003).

[43] M. R. VanLandingham, C. C. White, N.-K. Chang and S.-H.Chang, Viscoelastic characterization of polymers using instru mented indentation—Dynamic testing, J. Mater. Res., submit ted (2003).

[44] ISO group TC 164/SC 3/WG 1 and ASTM E28.06.11, Metallic materials—Instrumented indentation test for hardness and materials parameters, ISO/DIS 14577-1, 2, and 3.

[45] Z. L. Jabbour and S. L. Yaniv, The Kilogram and the measure ments of mass and force, J. Res. Natl. Inst. Stand. Technol. 106,25-46 (2001).

[46] E. R. Williams, R. L. Steiner, D. B. Newell, and P. T. Olsen,Accurate measurement of the Planck constant, Phys. Rev. Lett.81, 2404-2407 (1998).

[47] T. Funck and V. Sienknecht, Determination of the Volt with the improved PTB Voltage Balance, IEEE Trans. Inst. Meas. 40(2),158-161 (1991).

[48] D. B. Newell, J. A. Kramar, J. R. Pratt, D. T. Smith, and E. R.Williams, The NIST Microforce Realization and Measurement project, in IEEE Proceedings on Instrumentation and Measurement–CPEM special issue (2003) in press.

[49] J. A. Kramar, D. B. Newell, and J. R. Pratt, NIST Electro static Force Balance experiment, in Proceedings of the Joint International Conference IMEKO TC3/TC5/TC20,VDI-Berichte 1685 (2002) 71-76.

[50] J. L. Meneve, J. F. Smith, N. M. Jennett, and S. R. J. Saunders,Surface mechanical property testing by depth sensing indenta tion, Appl. Surf. Sci. 100/101, 64-68 (1998).

[51] M. R. VanLandingham, J. S. Villarrubia, and G. F. Meyers,Recent Progress in Nanoscale Indentation of Polymers Using the AFM, in Proceedings of the SEM IX International Congress on Experimental Mechanics, Society for Engineering Mechanics, Inc., Bethel, CT (2000) 912-915. 

[52] M. R. VanLandingham, J. S. Villarrubia, and R. Camara,Measuring tip shape for instrumented indentation using the atomic force microscope, J. Mater. Res., submitted (2003).

[53] K. W. McElhaney, J. J. Vlassak, and W. D. Nix, Determination of indenter tip geometry and indentation contact area for depth sensing indentation experiments, J. Mater. Res. 13 (5), 13001306 (1998).

[54] J. Thurn and R.F. Cook, Simplified area function for sharp indenter tips in depth-sensing indentation, J. Mater. Res. 17 (5),1143-1146 (2002).

[55] Y. Sun, S. Zheng, T. Bell, and J. Smith, Indenter tip radius and load frame compliance calibration using nanoindentation load ing curves, Phil. Mag. Lett. 79 (9), 649-658 (1999).

[56] M. R. VanLandingham, N.-K. Chang, C. C. White, and S.-H.Chang, Viscoelastic characterization of polymers using instru mented indentation—Quasi-static testing, J. Mater. Res., sub mitted (2003).

[57] J. S. Villarrubia, Morphological estimation of tip geometry for scanned probe microscopy, Surf. Sci. 321 (3), 287-300 (1994).

[58] J. S. Villarrubia, Algorithms for scanned probe microscope image simulation, surface reconstruction, and tip estimation,J. Res. Natl. Inst. Stand. Technol. 102 (4), 425-454 (1997).

[59] R. Dison, R. Köning, J. Fu, T. Vorburger, and B. Renegar,Accurate dimensional metrology with atomic force microscopy, SPIE Proc. 3998, 362-368 (2000).

[60] J. D. Ferry, Viscoelastic Properties of Polymers, John Wiley &Sons, Inc., New York (1980).

[61] T. C. T. Ting, Contact stresses between a rigid indenter and a viscoelastic half-space, J. Appl. Mech. 33 (4), 845-854 (1966).

About the author: Mark R. VanLandingham was formerly a materials research engineer in the Materials and Construction Research Division of the NIST Building and Fire Research Laboratory and is current ly a materials engineer in the Polymers Research Branch of the Army Research Laboratory, Weapons and Materials Research Directorate. The National Institute of Standards and Technology is an agency of the Technology Administration, U.S. Department of Commerce, and the Army Research Laboratory is a major subordinate command of the U.S. Army Research and Development Engineering Command, U.S.Department of the Army, U.S. Department of Defense.

<!-- 265 -->



