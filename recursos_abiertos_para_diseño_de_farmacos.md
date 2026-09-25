# Inventario de Recursos Abiertos para Diseño de Fármacos (Sabueso / UIBCDF)

Este documento recopila recursos abiertos, bases de datos y repositorios bioinformáticos y quimioinformáticos relevantes para campañas de diseño de fármacos (*Structure-Based* y *Ligand-Based Drug Design*). Sirve como catálogo estructurado para evaluar viabilidad de APIs, esquemas de datos e interoperabilidad en **Sabueso**.

---

## 1. Dianas, Secuencia y Farmacología Básica

| Recurso | Descripción | Enlace |
|---|---|---|
| **UniProt** | Fuente canónica de secuencia de proteínas, isoformas, dominios, sitios activos y variantes. | [uniprot.org](https://www.uniprot.org/) |
| **Guide to PHARMACOLOGY (IUPHAR/BPS)** | Relaciones diana-ligando curadas por comités expertos, clasificación cuantitativa de agonistas/antagonistas y selectividad clínica. | [guidetopharmacology.org](https://www.guidetopharmacology.org/) |
| **NCBI Gene / RefSeq** | Metadatos genómicos, ortología, identificadores estandarizados y secuencias nucleotídicas. | [ncbi.nlm.nih.gov/gene](https://www.ncbi.nlm.nih.gov/gene/) |
| **Ensembl** | Anotación de genes, transcritos, homología y variantes poblacionales integradas. | [ensembl.org](https://www.ensembl.org/) |
| **InterPro / Pfam** | Clasificación funcional de proteínas en familias, dominios conservados y sitios catalíticos/de unión. | [ebi.ac.uk/interpro](https://www.ebi.ac.uk/interpro/) |

---

## 2. Validación de Dianas, Genética y Redes Funcionales

| Recurso | Descripción | Enlace |
|---|---|---|
| **Open Targets Platform** | Evidencia integrada de asociación gen-enfermedad, tractabilidad para small molecules/biológicos y datos preclínicos. | [platform.opentargets.org](https://platform.opentargets.org/) |
| **TTD (Therapeutic Target Database)** | Dianas moleculares (proteínas y ácidos nucleicos), estado clínico, patologías y mutaciones de resistencia. | [idrblab.org/ttd](https://idrblab.org/ttd/) |
| **DGIdb** | Drug-Gene Interaction Database: agregador de interacciones fármaco-gen y categorías de *druggability*. | [dgidb.org](https://dgidb.org/) |
| **DepMap** | Cancer Dependency Map: cribados CRISPR y RNAi para evaluar esencialidad génica y dependencias sintéticas. | [depmap.org](https://depmap.org/) |
| **Reactome** | Base curada de rutas biológicas humanas, reacciones metabólicas y redes de señalización (API REST). | [reactome.org](https://reactome.org/) |
| **KEGG PATHWAY** | Diagramas de rutas metabólicas, cascadas de transducción celular y enfermedades humanas. | [kegg.jp](https://www.kegg.jp/) |
| **ClinVar** | Variantes genómicas humanas y su correlación clínica/patogénica. | [ncbi.nlm.nih.gov/clinvar](https://www.ncbi.nlm.nih.gov/clinvar/) |
| **gnomAD** | Frecuencias alélicas y variabilidad poblacional para evaluar conservación del bolsillo de unión. | [gnomad.broadinstitute.org](https://gnomad.broadinstitute.org/) |
| **PharmacoDB** | Armonización de estudios masivos de cribado farmacogenómico y curvas dosis-respuesta celulares. | [pharmacodb.pmgenomics.ca](https://pharmacodb.pmgenomics.ca/) |

---

## 3. Interacciones Proteína-Proteína (PPI) y Modulación Estructural

| Recurso | Descripción | Enlace |
|---|---|---|
| **STRING** | Redes de interacción física y funcional proteína-proteína con puntuaciones probabilísticas de confianza (API REST sólida). | [string-db.org](https://string-db.org/) |
| **IntAct (EMBL-EBI)** | Base curada de evidencia experimental de interacciones binarias moleculares directas (estándar PSI-MI). | [ebi.ac.uk/intact](https://www.ebi.ac.uk/intact/) |
| **BioGRID** | Repositorio de interacciones biológicas genéticas y proteicas derivadas de literatura curada. | [thebiogrid.org](https://thebiogrid.org/) |
| **2P2Idb** | Base estructural curada de complejos proteína-proteína modulados por pequeñas moléculas ortostéricas, con parámetros de interfaz y cálculo de druggability. | [2p2idb.cnrs-mrs.fr](http://2p2idb.cnrs-mrs.fr/) |
| **iPPI-DB** | Base de datos de inhibidores y moduladores no peptídicos de PPIs con caracterización farmacológica, quimioinformática y estructural. | [ippidb.pasteur.fr](https://ippidb.pasteur.fr/) |
| **SKEMPI 2.0** | Variación cuantitativa de afinidad de unión ($\Delta\Delta G$) y constantes cinéticas generadas por mutaciones en interfaces PPI. | [life.bsc.es/pid/skempi2](https://life.bsc.es/pid/skempi2/) |
| **PPI3D** | Búsqueda, análisis y modelado de interfaces de interacción intercadena y complejos macromoleculares basados en teselación de Voronoi. | [bioinformatics.ibt.lt/ppi3d](http://bioinformatics.ibt.lt/ppi3d/) |

---

## 4. Estructura Macromolecular, Modelos y Dinámica

| Recurso | Descripción | Enlace |
|---|---|---|
| **RCSB PDB / PDBe / PDBj** | Archivo primario de estructuras 3D experimentales (rayos X, crio-EM, RMN), factores de anisotropía y ensamblajes biológicos. | [rcsb.org](https://www.rcsb.org/) / [ebi.ac.uk/pdbe](https://www.ebi.ac.uk/pdbe/) |
| **AlphaFold DB** | Predicciones estructurales monoméricas y complejas con métricas de calidad por residuo ($pLDDT$) y posicional ($PAE$). | [alphafold.ebi.ac.uk](https://alphafold.ebi.ac.uk/) |
| **ModelArchive** | Repositorio abierto de modelos computacionales de macromoléculas con metadatos según estándar mmCIF. | [modelarchive.org](https://modelarchive.org/) |
| **ESM Metagenomic Atlas** | Estructuras predichas a escala masiva por modelos de lenguaje de proteínas (Meta AI). | [esmatlas.com](https://esmatlas.com/) |
| **NDB (Nucleic Acid Database)** | Estructuras tridimensionales y conformaciones de ácidos nucleicos (ARN/ADN) y sus complejos con ligandos o proteínas. | [ndbserver.rutgers.edu](https://ndbserver.rutgers.edu/) |
| **CoDNaS** | Conformational Diversity of Native State: catálogo de confórmeros experimentales en el PDB para analizar plasticidad de la diana. | [codnas.inf.unlp.edu.ar](https://codnas.inf.unlp.edu.ar/) |
| **MoDEL Library** | Repositorio estandarizado de trayectorias y conformaciones de simulación por dinámica molecular atomística. | [mmb.irbbarcelona.org/MoDEL](https://mmb.irbbarcelona.org/MoDEL/) |
| **ProThermDB** | Datos termodinámicos experimentales de estabilidad de proteínas y variaciones ($\Delta\Delta G$, $T_m$) ante mutaciones puntuales. | [web.iitm.ac.in/bioinfo2/prothermdb](https://web.iitm.ac.in/bioinfo2/prothermdb/) |

---

## 5. Bolsillos de Unión, Cavidades y Familias Especializadas

| Recurso | Descripción | Enlace |
|---|---|---|
| **sc-PDB** | Sitios de unión farmacológicamente relevantes extraídos del PDB, limpios de artefactos cristalográficos y con cavidades acotadas. | [bioinfo-pharma.u-strasbg.fr/scPDB](http://bioinfo-pharma.u-strasbg.fr/scPDB/) |
| **BioLiP** | Compendio exhaustivo y curado de interacciones funcionales macromolécula-ligando. | [zhanggroup.org/BioLiP](https://zhanggroup.org/BioLiP/) |
| **Binding MOAD** | Complejos resueltos de alta resolución ligados a datos de afinidad biológicamente validados. | [bindingmoad.org](https://bindingmoad.org/) |
| **ASD (Allosteric Database)** | Información centralizada sobre moduladores alostéricos, sitios reguladores y comunicación conformacional. | [mdl.shsmu.edu.cn/ASD](http://mdl.shsmu.edu.cn/ASD/) |
| **KLIFS** | Desglose anatómico del bolsillo de quinasas alineado a 85 posiciones de referencia y clasificación conformacional DFG/$\alpha\text{C}$. | [klifs.net](https://klifs.net/) |
| **GPCRdb** | Datos estructurales, mutacionales, estados de activación y numeración Ballesteros-Weinstein para receptores acoplados a proteína G. | [gpcrdb.org](https://gpcrdb.org/) |
| **OPM (Orientations of Proteins in Membranes)** | Localización y orientación espacial de estructuras del PDB dentro de la bicapa lipídica teórica. | [opm.phar.umich.edu](https://opm.phar.umich.edu/) |
| **mpstruc** | Proteínas de membrana con estructura 3D resuelta clasificadas por topología y familia. | [blanco.biomol.uci.edu/mpstruc](https://blanco.biomol.uci.edu/mpstruc/) |
| **M-CSA (Mechanism and Catalytic Site Atlas)** | Catálogo curado de mecanismos de reacción enzimática, residuos catalíticos y funciones de cofactores con soporte PDB. | [ebi.ac.uk/thornton-srv/m-csa](https://www.ebi.ac.uk/thornton-srv/m-csa/) |
| **BRENDA** | Sistema de información enzimática comprehensivo: datos cinéticos ($K_m$, $k_{cat}$), inhibidores, cofactores y condiciones óptimas. | [brenda-enzymes.org](https://brenda-enzymes.org/) |
| **SABIO-RK** | Constantes cinéticas de reacciones bioquímicas purificadas bajo condiciones experimentales controladas (API REST). | [sabiork.h-its.org](http://sabiork.h-its.org/) |
| **CovPDB** | Base de datos de complejos covalentes proteína-ligando anotando residuos nucleofílicos y *warheads* reactivos. | [bioinfo.fudan.edu.cn/CovPDB](https://bioinfo.fudan.edu.cn/CovPDB/) |
| **SAbDab / Thera-SAbDab** | Estructuras de anticuerpos y nanocuerpos con numeración estándar (Chothia/IMGT), CDRs identificadas y metadatos clínicos. | [opig.stats.ox.ac.uk/webapps/sabdab](https://opig.stats.ox.ac.uk/webapps/sabdab/) |
| **Proteins.plus (DoGSiteScorer)** | Plataforma de detección de bolsillos crípticos, descriptores fisicoquímicos y puntuación de tractabilidad. | [proteins.plus](https://proteins.plus/) |

---

## 6. Afinidad Termodinámica y Bioactividad Experimental

| Recurso | Descripción | Enlace |
|---|---|---|
| **ChEMBL** | Base de datos de referencia para moléculas bioactivas, ensayos funcionales/bioquímicos y afinidades cuantitativas ($IC_{50}$, $K_i$). | [ebi.ac.uk/chembl](https://www.ebi.ac.uk/chembl/) |
| **BindingDB** | Enfoque directo en afinidades termodinámicas de equilibrio físico ($K_i$, $K_d$) y datos calorimétricos de ITC. | [bindingdb.org](https://www.bindingdb.org/) |
| **PDBbind-CN** | Complejos resueltos en 3D emparejados con afinidades termodinámicas experimentales calibradas (*Core* y *Refined Sets*). | [pdbbind.org.cn](http://www.pdbbind.org.cn/) |
| **PubChem BioAssay** | Resultados masivos de cribado HTS, cribados fenotípicos y curvas dosis-respuesta biológicas. | [pubchem.ncbi.nlm.nih.gov](https://pubchem.ncbi.nlm.nih.gov/) |

---

## 7. Benchmarking, Desafíos Abiertos y Consorcios de Ciencia Abierta

| Recurso | Descripción | Enlace |
|---|---|---|
| **D3R (Drug Design Data Resource)** | Conjuntos de datos y desafíos a ciegas con afinidades experimentales rigurosas para docking y predicción de energía libre (FEP). | [drugdesigndata.org](https://drugdesigndata.org/) |
| **CACHE Challenge** | Desafíos de cribado computacional ciego con validación experimental independiente de aciertos y falsos positivos en abierto. | [cache-challenge.org](https://cache-challenge.org/) |
| **OpenBind** | Iniciativa para generar grandes conjuntos abiertos de estructuras ligando-proteína y perfiles de afinidad para IA biofísica. | [openbind.uk](https://openbind.uk/) |
| **Therapeutics Data Commons (TDC)** | Plataforma de referencia y datasets estandarizados *AI-ready* para diseño de fármacos, afinidad y perfiles ADMET. | [tdcommons.ai](https://tdcommons.ai/) |
| **CSAR** | Community Structure-Activity Resource: complejos cristalográficos de alta resolución para evaluar funciones de puntuación. | [csardock.org](http://www.csardock.org/) |
| **PoseBusters** | Benchmarks y pruebas de control de calidad para validar la física, estereoquímica y ausencia de choques en poses de acoplamiento. | [github.com/maabuu/posebusters](https://github.com/maabuu/posebusters) |
| **Fragalysis / XChem** | Datos cristalográficos directos de campañas abiertas de cribado por fragmentos en el sincrotrón Diamond. | [fragalysis.diamond.ac.uk](https://fragalysis.diamond.ac.uk/) |
| **COVID Moonshot / ASAP Discovery** | Descubrimiento colaborativo abierto: series químicas optimizadas, afinidades enzimáticas, síntesis y rayos X sin barreras de IP. | [asapdiscovery.org](https://asapdiscovery.org/) |
| **RNA-Puzzles** | Evaluación comunitaria ciega para predicción de estructuras terciarias de ARN. | [rnapuzzles.org](https://rnapuzzles.org/) |
| **Target 2035 / SGC** | Caracterización de sondas químicas (*chemical probes*) selectivas y controles negativos para dianas poco exploradas. | [target2035.net](https://target2035.net/) / [thesgc.org](https://www.thesgc.org/) |

---

## 8. Modalidades Emergentes y Degradación Dirigida (PROTACs)

| Recurso | Descripción | Enlace |
|---|---|---|
| **PROTAC-DB** | Base de datos de quimeras dirigidas a proteólisis: ligasas E3, warheads, linkers, ternarios y datos cuantitativos de degradación ($DC_{50}$, $D_{max}$). | [cadd.zju.edu.cn/protacdb](http://cadd.zju.edu.cn/protacdb/) |

---

## 9. Espacio Químico, Síntesis y ADMET / Seguridad

| Recurso | Descripción | Enlace |
|---|---|---|
| **DrugBank (Open Access Data)** | Farmacología de fármacos aprobados y experimentales, metabolismo, transportadores y mecanismos de acción. | [go.drugbank.com](https://go.drugbank.com/) |
| **SureChEMBL** | Estructuras químicas y patentes globales extraídas sistemáticamente mediante text mining automatizado. | [surechembl.org](https://surechembl.org/) |
| **ZINC (ZINC20 / ZINC-22)** | Modelos tridimensionales de compuestos comerciales y sintetizables *on-demand* preparados para cribado virtual masivo. | [zinc.docking.org](https://zinc.docking.org/) |
| **Enamine REAL Space** | Catálogo combinatorial de miles de millones de moléculas sintetizables bajo demanda mediante protocolos validados. | [enamine.net/compound-collections/real-compounds](https://enamine.net/compound-collections/real-compounds) |
| **ChEBI** | Ontología estructurada de entidades químicas, metabolitos endógenos y cofactores biológicos. | [ebi.ac.uk/chebi](https://www.ebi.ac.uk/chebi/) |
| **Tox21 / ToxCast (EPA / PubChem)** | Perfiles de cribado fenotípico y enzimático de toxicidad celular *in vitro*, estrés biológico y falsos positivos de ensayo. | [epa.gov/chemical-research/toxicity-forecasting](https://www.epa.gov/chemical-research/toxicity-forecasting) |

---

## 10. Ecosistemas de Código Abierto Relacionados

| Recurso | Descripción | Enlace |
|---|---|---|
| **TeachOpenCADD** | Flujos de trabajo computacionales reproducibles en Python para quimioinformática y modelado molecular. | [projects.volkamerlab.org/teachopencadd](https://projects.volkamerlab.org/teachopencadd/) |
| **ProLIF** | Fingerprints de interacción proteína-ligando en 3D para trayectorias de dinámica molecular y complejos estáticos. | [prolif.readthedocs.io](https://prolif.readthedocs.io/) |
| **Open Drug Discovery Toolkit (ODDT)** | Herramientas en Python para cribado virtual, scoring empírico y manipulación de coordenadas químicas. | [github.com/oddt/oddt](https://github.com/oddt/oddt) |