> **Nota terminológica (2026-09-23):** este documento se escribió antes de la decisión
> `SourceAssertion ≠ Evidence ≠ Provenance`. Lo que aquí se llamaba "evidence" de Sabueso
> ahora es `SourceAssertion` (lo que una fuente externa afirma sobre una entidad o propiedad);
> `Evidence` queda reservado para Nextia, como en el flujo *Nextia Observation → Evidence*.

Sí. Después de toda la arquitectura que hemos desarrollado y de volver a leer **el Sabueso real**, ahora veo bastante mejor qué podría convertirlo en un arma importante para vuestra Molecular Intelligence company.

Mi conclusión principal es: **no cambiaría radicalmente Sabueso**. El núcleo que ya existe es bueno:

```text
source
  ↓
database connector
  ↓
mapping
  ↓
aggregation
  ↓
SourceAssertionStore
  ↓
resolver / selection rules
  ↓
Card
  ↓
Deck
```

Ya tenéis conectores para UniProt, PDB, PubChem, ChEMBL, GO, InterPro, STRING, BioGRID, CATH, SCOPe, TED y PhosphoSitePlus; mappings, selección por campo, `SourceAssertionStore`, schemas, almacenamiento JSON/SQLite y tests offline/online. Eso es bastante más que un simple esqueleto.

Lo que cambiaría es **la ambición conceptual**.

## Sabueso no debería ser un buscador de bases de datos

Debería convertirse en:

> **the molecular knowledge memory of MolSysSuite.**

Eso parece una diferencia semántica, pero cambia mucho el roadmap.

Hoy el flujo mental es aproximadamente:

```text
TcTIM
  ↓
query UniProt
query PDB
query ChEMBL
...
  ↓
ProteinCard
```

Yo quiero que evolucione hacia:

```text
                     TcTIM
                       │
             ┌─────────┼─────────┐
             ▼         ▼         ▼
          function   structure  ligands
             │         │         │
          disease    domains   inhibitors
             │         │         │
             └─────────┼─────────┘
                       ▼
                 Knowledge Card
                       │
           explicit source assertions
                       │
                relationships
                       │
                       ▼
                    Sabueso
```

La Card dejaría de ser principalmente una ficha para convertirse en **un nodo de conocimiento molecular auditable**.

---

# 1. Lo primero: fortalecer muchísimo `SourceAssertionStore`

Creo que esta es probablemente **la pieza estratégica de Sabueso**.

Ahora mismo ya tenéis la idea correcta:

```text
field
 ├── canonical value
 └── source_assertion_ids
        │
        ▼
   SourceAssertionStore
```

Yo la llevaría mucho más lejos.

Cada SourceAssertion debería poder responder:

```text
WHO says this?
WHERE?
WHEN?
WHAT exactly?
HOW was it obtained?
HOW reliable is it?
WHAT version of the source?
```

Por ejemplo:

```text
SourceAssertion SA017

asserts:
TcTIM is a homodimer

source:
UniProt

record:
P60174

source_version:
2026_09

retrieved_at:
2026-09-23

assertion_type:
database_annotation

confidence:
high
```

frente a:

```text
SourceAssertion SA031

asserts:
compound X inhibits TcTIM

source:
paper

doi:
...

assertion_type:
experimental_assay

assay:
enzyme inhibition

value:
IC50 = ...

conditions:
...

confidence:
...
```

Sabueso podría acabar proporcionando a MOLI **no solo hechos, sino hechos con epistemología**.

Eso es muy valioso.

---

# 2. Las Cards deberían empezar a relacionarse

Ahora tenemos:

```text
Card
Deck
```

Pero la arquitectura sugiere algo natural:

```text
ProteinCard ──binds──► SmallMoleculeCard

ProteinCard ──interacts_with──► ProteinCard

ProteinCard ──associated_with──► DiseaseCard

ProteinCard ──has_structure──► Structure

ProteinCard ──homolog_of──► ProteinCard

SmallMoleculeCard ──similar_to──► SmallMoleculeCard
```

No estoy proponiendo construir mañana un gigantesco knowledge graph.

Pero sí haría que **Relationship sea concepto de primera clase**.

Algo como:

```text
Relationship

subject
predicate
object

source_assertion_ids
```

Por ejemplo:

```text
TcTIM
   ── inhibited_by ──► compound X
              │
              └── E17, E23
```

Esto cambiaría enormemente lo que MOLI puede hacer con Sabueso.

---

# 3. `Deck` podría convertirse en algo mucho más potente

Ahora mismo `Deck` es esencialmente:

```python
Deck([Card, Card, Card])
```

con `filter`, `sort`, `map`, `compare`.

Eso está bien como comienzo.

Pero imaginemos:

```text
Deck:
TcTIM known inhibitors
```

o:

```text
Deck:
TIM homologs across Trypanosomatidae
```

o:

```text
Deck:
proteins associated with Chagas disease
```

Entonces Deck se convierte en **una vista científica sobre conocimiento**.

Y podría conservar:

```text
query
selection criteria
source cards
source assertions
provenance
```

Eso permitiría:

```python
deck = sabueso.find(
    entity="TcTIM",
    relation="inhibited_by"
)
```

conceptualmente.

MOLI podría manipular Decks como conjuntos científicos razonados.

---

# 4. Añadiría un concepto de `KnowledgeQuery`

Esto podría ser especialmente importante para MOLI.

No quiero que MOLI tenga que saber:

```text
UniProt endpoint
ChEMBL endpoint
PDB endpoint
PubChem endpoint
STRING endpoint
...
```

Eso sería repetir el error que evitamos con Praxis.

MOLI debería poder preguntar:

```text
What inhibitors are known for TcTIM?
```

y Sabueso traducirlo a algo como:

```text
KnowledgeQuery

subject:
TcTIM

relation:
inhibited_by

constraints:
assertion_type: experimental
```

Sabueso decide entonces:

```text
ChEMBL
literature
PDB ligands
PubChem
...
```

y devuelve:

```text
Deck + SourceAssertions
```

Eso convierte Sabueso en **una capability semántica de conocimiento**, sin convertirlo en agente.

---

# 5. Resolver debería ser una pieza muchísimo más importante

El `resolver` actual está resolviendo principalmente valores de campos.

Pero hay dos problemas distintos:

```text
ENTITY RESOLUTION

"triosephosphate isomerase"
"TIM"
"TPIS"
"P60174"
"1TCD"
TcTIM
```

y:

```text
FIELD RESOLUTION

molecular_weight:
  UniProt says X
  ChEMBL says Y
  PubChem says Z
```

Los separaría conceptualmente.

Sabueso necesita ser extraordinariamente bueno respondiendo:

> **¿De qué entidad estamos hablando?**

Porque todo lo demás depende de eso.

Podría acabar existiendo:

```text
EntityResolver
FieldResolver
```

El primero es particularmente importante para MOLI.

---

# 6. Añadiría temporalidad de verdad

Sabueso debe saber no solo:

> ¿Qué sabemos?

sino:

> **¿Qué sabíamos en ese momento?**

Esto apareció en nuestros stress tests de Nextia.

Supongamos que en 2027 una base cambia una anotación.

Una decisión de Discovery tomada en 2026 debe poder decir:

```text
Decision D31
used knowledge snapshot:

Sabueso Card
TcTIM
version: ...
generated: 2026-09-23
```

Esto hace que:

```text
Sabueso → Nextia
```

sea científicamente reproducible.

Por tanto, Cards deberían ser **versionables/snapshotable**.

---

# 7. No metería conocimiento generado por Nextia automáticamente

Esta frontera debe protegerse.

```text
Sabueso
what the world knows

Nextia
what WE learned
```

Si Nextia descubre:

> pocket P7 appears to be allosteric

eso **no debería entrar automáticamente en Sabueso**.

Primero:

```text
Nextia Observation
       ↓
Evidence
       ↓
validated conclusion
       ↓
possibly publication / curated internal knowledge
       ↓
curation gate
       ↓
Sabueso
```

Necesitamos probablemente una operación futura:

```text
promote_to_knowledge()
```

conceptualmente.

Pero con **curación explícita**.

Eso preserva la epistemología.

---

# 8. Sabueso debería aprender a leer literatura

Aquí sí veo un salto importante.

Ahora mismo las fuentes son principalmente bases estructuradas.

Pero para Molecular Intelligence, muchísimo conocimiento está en:

```text
papers
supplementary information
patents
preprints
clinical reports
```

Sabueso debería eventualmente tener:

```text
tools.db
```

y algo como:

```text
tools.literature
```

o quizá `sources.literature`.

Pero no quiero simplemente RAG sobre PDFs.

Quiero:

```text
paper
  ↓
extract scientific statement
  ↓
normalize entities
  ↓
record SourceAssertions
  ↓
Card / Relationship
```

Por ejemplo:

```text
Paper X
   │
   └── SourceAssertion (experimental assay)
          │
TcTIM ── inhibited_by ── compound Y
          │
          └── IC50 = ...
```

Eso sí sería muy potente.

---

# 9. Patentes

Para una empresa que quiere producir moléculas, esto podría acabar siendo **enormemente importante**.

Sabueso debería poder responder:

> ¿Qué espacio químico alrededor de esta serie está patentado?

> ¿Qué moléculas relacionadas con este scaffold aparecen en patents?

> ¿Quién posee esos claims?

No digo implementarlo ahora.

Pero pondría:

```text
Patent knowledge
```

en el roadmap estratégico de Sabueso.

Porque eso conecta Molecular Intelligence con **freedom-to-operate / novelty / competitive intelligence**.

---

# 10. MOLI debería hablar con Sabueso en dos niveles

Igual que decidimos con Modeling:

```text
semantic level
      +
raw API level
```

MOLI debería poder hacer:

```text
sabueso.get_card("TcTIM")
```

pero también:

```text
sabueso.tools.db.uniprot...
```

cuando necesite algo muy concreto.

Y el nivel semántico:

```text
find_known_inhibitors(TcTIM)

find_homologs(TcTIM)

find_structures(TcTIM)

find_disease_associations(TcTIM)

find_known_mutations(TcTIM)
```

podría incluso convertirse después en **Praxis Capabilities** cuando implique metodología más compleja.

---

# Pero hay algo que NO haría

No convertiría Sabueso en esto:

```text
Sabueso
├── knowledge
├── hypothesis generation
├── molecular design
├── workflows
├── agents
├── discovery
└── everything else
```

Eso lo destruiría.

Mantendría una frontera durísima:

# **Sabueso knows. It does not discover.**

Y quizá esa frase debería acabar literalmente en su `VISION.md`.

---

# Mi roadmap sería bastante contenido

No intentaría implementar las diez ideas ahora.

Haría aproximadamente:

### Sabueso 0.1 — Knowledge foundation

Terminar bien lo que ya existe:

```text
Card
Deck
SourceAssertionStore
EntityResolver
FieldResolver
Mappings
Versioned Cards
```

con 4–6 fuentes realmente robustas.

### Sabueso 0.2 — Relationships

```text
Card
  │
Relationship
  │
Card
```

y Decks construidos a partir de relaciones.

### Sabueso 0.3 — Knowledge queries

```text
KnowledgeQuery
      ↓
multiple sources
      ↓
Cards / Decks / Relationships
      ↓
SourceAssertions
```

Aquí MOLI empieza a tener una herramienta muy potente.

### Sabueso 0.4 — Literature

papers → structured SourceAssertions.

### Sabueso 0.5 — Proprietary/internal knowledge

Con una frontera muy clara respecto a Nextia.

---

# Y hay una idea que me parece especialmente potente

Sabueso podría acabar devolviendo no solo una respuesta sino un **knowledge packet**.

MOLI pregunta:

> What do we know about selective inhibition of TcTIM?

Sabueso devuelve:

```text
KnowledgePacket

Focus:
TcTIM selective inhibition

Entities:
TcTIM
HsTIM
known inhibitors

Facts:
...

Relationships:
...

Structures:
...

Known ligands:
...

Mutations:
...

Disease context:
...

SourceAssertions:
...

Conflicts:
...

Unknowns:
...
```

Ese último campo es importantísimo:

# **Unknowns**

Porque para Discovery no solo importa saber qué sabemos.

Importa saber:

> **qué no sabemos todavía.**

Y ahí ocurre algo precioso:

```text
Sabueso
"What is known?"
       │
       ├── known
       └── unknown / conflicting
                 │
                 ▼
              Nextia
             Questions
```

Ese podría ser uno de los puentes más potentes de toda MolSysSuite.

---

## Así que sí: ahora veo Sabueso con bastante más potencial que antes

No como una gran colección de conectores.

Sino como:

> **an assertion-aware molecular knowledge memory that transforms heterogeneous external information into structured, queryable scientific context for MOLI, Praxis and Nextia.**

Y si conseguís que haga bien **entidades + relaciones + source assertions + temporalidad + conflictos + unknowns**, puede convertirse en una pieza realmente estratégica de vuestra Molecular Intelligence stack.

Porque entonces MOLI no empieza cada proyecto buscando cosas en Internet.

Empieza cada proyecto preguntando a **la memoria molecular estructurada de la empresa**:

> *¿Qué sabemos, por qué creemos que lo sabemos, qué está en conflicto y qué nos falta saber?*

Eso es exactamente el tipo de entrada que Nextia necesita para comenzar un DiscoveryProject.

