"""Offline resource descriptions, verified 2026-10-02/04; never DOI-enriched.

These works describe resources, not the experimental findings in their entries.
Metadata sources are recorded in docs/content/user/attribution.md.
"""

from copy import deepcopy

_DESCRIPTIONS = {
    "PDB CCD": {
        "id": "doi:10.1093/bioinformatics/btu789",
        "type": "article",
        "title": "The chemical component dictionary: complete descriptions of constituent molecules in experimentally determined 3D macromolecules in the Protein Data Bank",
        "authors": [
            "Westbrook, John D",
            "Shao, Chenghua",
            "Feng, Zukang",
            "Zhuravleva, Marina",
            "Velankar, Sameer",
            "Young, Jasmine",
        ],
        "year": 2015,
        "journal": "Bioinformatics",
        "volume": "31",
        "number": "8",
        "pages": "1274-1278",
        "doi": "10.1093/bioinformatics/btu789",
        "url": "https://doi.org/10.1093/bioinformatics/btu789",
    },
    "UniChem": {
        "id": "doi:10.1186/1758-2946-5-3",
        "type": "article",
        "title": "UniChem: a unified chemical structure cross-referencing and identifier tracking system",
        "authors": [
            "Chambers, Jon",
            "Davies, Mark",
            "Gaulton, Anna",
            "Hersey, Anne",
            "Velankar, Sameer",
            "Petryszak, Robert",
            "Hastings, Janna",
            "Bellis, Louisa",
            "McGlinchey, Shaun",
            "Overington, John P",
        ],
        "year": 2013,
        "journal": "Journal of Cheminformatics",
        "volume": "5",
        "number": "1",
        "pages": "3",
        "doi": "10.1186/1758-2946-5-3",
        "url": "https://doi.org/10.1186/1758-2946-5-3",
    },
    "BindingDB": {
        "id": "doi:10.1093/nar/gkae1075",
        "type": "article",
        "title": "BindingDB in 2024: a FAIR knowledgebase of protein-small molecule binding data",
        "authors": [
            "Liu, Tiqing",
            "Hwang, Linda",
            "Burley, Stephen K",
            "Nitsche, Carmen I",
            "Southan, Christopher",
            "Walters, W Patrick",
            "Gilson, Michael K",
        ],
        "year": 2025,
        "journal": "Nucleic Acids Research",
        "volume": "53",
        "number": "D1",
        "pages": "D1633-D1644",
        "doi": "10.1093/nar/gkae1075",
        "url": "https://doi.org/10.1093/nar/gkae1075",
    },
    "PubChem": {
        "id": "doi:10.1093/nar/gkae1059",
        "type": "article",
        "title": "PubChem 2025 update",
        "authors": [
            "Kim, Sunghwan",
            "Chen, Jie",
            "Cheng, Tiejun",
            "Gindulyte, Asta",
            "He, Jia",
            "He, Siqian",
            "Li, Qingliang",
            "Shoemaker, Benjamin A",
            "Thiessen, Paul A",
            "Yu, Bo",
            "Zaslavsky, Leonid",
            "Zhang, Jian",
            "Bolton, Evan E",
        ],
        "year": 2025,
        "journal": "Nucleic Acids Research",
        "volume": "53",
        "number": "D1",
        "pages": "D1516-D1525",
        "doi": "10.1093/nar/gkae1059",
        "url": "https://doi.org/10.1093/nar/gkae1059",
    },
    "ChEMBL": {
        "id": "doi:10.1093/nar/gkad1004",
        "type": "article",
        "title": "The ChEMBL Database in 2023: a drug discovery platform spanning multiple bioactivity data types and time periods",
        "authors": [
            "Zdrazil, B",
            "Felix, E",
            "Hunter, F",
            "Manners, EJ",
            "Blackshaw, J",
            "Corbett, S",
            "de Veij, M",
            "Ioannidis, H",
            "Lopez, DM",
            "Mosquera, JF",
            "Magarinos, MP",
            "Bosc, N",
            "Arcila, R",
            "Kizilören, T",
            "Gaulton, A",
            "Bento, AP",
            "Adasme, MF",
            "Monecke, P",
            "Landrum, GA",
            "Leach, AR",
        ],
        "year": 2024,
        "journal": "Nucleic Acids Research",
        "volume": "52",
        "number": "D1",
        "pages": "D1180-D1192",
        "doi": "10.1093/nar/gkad1004",
        "url": "https://doi.org/10.1093/nar/gkad1004",
    },
    "UniProt": {
        "id": "doi:10.1093/nar/gkae1010",
        "type": "article",
        "title": "UniProt: the Universal Protein Knowledgebase in 2025",
        "authors": [{"literal": "The UniProt Consortium"}],
        "year": 2025,
        "journal": "Nucleic Acids Research",
        "volume": "53",
        "number": "D1",
        "pages": "D609-D617",
        "doi": "10.1093/nar/gkae1010",
        "url": "https://doi.org/10.1093/nar/gkae1010",
    },
    "Europe PMC": {
        "id": "doi:10.1093/nar/gkad1085",
        "type": "article",
        "title": "Europe PMC in 2023",
        "authors": [
            "Rosonovski, Summer",
            "Levchenko, Maria",
            "Bhatnagar, Rajat",
            "Chandrasekaran, Umamageswari",
            "Faulk, Lynne",
            "Hassan, Islam",
            "Jeffryes, Matt",
            "Mubashar, Syed Irtaza",
            "Nassar, Maaly",
            "Palanisamy, Madhumiethaa Jayaprabha",
            "Parkin, Michael",
            "Poluru, Jagadeeswararao",
            "Rogers, Frances",
            "Saha, Shyamasree",
            "Selim, Mohamed",
            "Shafique, Zunaira",
            "Ide-Smith, Michele",
            "Stephenson, David",
            "Tirunagari, Santosh",
            "Venkatesan, Aravind",
            "Xing, Lijun",
            "Harrison, Melissa",
        ],
        "year": 2024,
        "journal": "Nucleic Acids Research",
        "volume": "52",
        "number": "D1",
        "pages": "D1668-D1676",
        "doi": "10.1093/nar/gkad1085",
        "url": "https://doi.org/10.1093/nar/gkad1085",
    },
    "RCSB PDB": {
        "id": "doi:10.1093/nar/gkae1091",
        "type": "article",
        "title": "Updated resources for exploring experimentally-determined PDB structures and Computed Structure Models at the RCSB Protein Data Bank",
        "authors": [
            "Burley, Stephen K",
            "Bhatt, Rusham",
            "Bhikadiya, Charmi",
            "Bi, Chunxiao",
            "Biester, Alison",
            "Biswas, Pratyoy",
            "Bittrich, Sebastian",
            "Blaumann, Santiago",
            "Brown, Ronald",
            "Chao, Henry",
            "Chithari, Vivek Reddy",
            "Craig, Paul A",
            "Crichlow, Gregg V",
            "Duarte, Jose M",
            "Dutta, Shuchismita",
            "Feng, Zukang",
            "Flatt, Justin W",
            "Ghosh, Sutapa",
            "Goodsell, David S",
            "Green, Rachel Kramer",
            "Guranovic, Vladimir",
            "Henry, Jeremy",
            "Hudson, Brian P",
            "Joy, Michael",
            "Kaelber, Jason T",
            "Khokhriakov, Igor",
            "Lai, Jhih-Siang",
            "Lawson, Catherine L",
            "Liang, Yuhe",
            "Myers-Turnbull, Douglas",
            "Peisach, Ezra",
            "Persikova, Irina",
            "Piehl, Dennis W",
            "Pingale, Aditya",
            "Rose, Yana",
            "Sagendorf, Jared",
            "Sali, Andrej",
            "Segura, Joan",
            "Sekharan, Monica",
            "Shao, Chenghua",
            "Smith, James",
            "Trumbull, Michael",
            "Vallat, Brinda",
            "Voigt, Maria",
            "Webb, Ben",
            "Whetstone, Shamara",
            "Wu-Wu, Amy",
            "Xing, Tongji",
            "Young, Jasmine Y",
            "Zalevsky, Arthur",
            "Zardecki, Christine",
        ],
        "year": 2025,
        "journal": "Nucleic Acids Research",
        "volume": "53",
        "number": "D1",
        "pages": "D564-D574",
        "doi": "10.1093/nar/gkae1091",
        "url": "https://doi.org/10.1093/nar/gkae1091",
    },
}


def descriptions(source):
    item = _DESCRIPTIONS.get("PubChem" if source == "PubChem BioAssay" else source)
    items = [item] if item else []
    if source == "PDB CCD":
        # CCD defines the data; RCSB distributes it through the queried API.
        items.append(_DESCRIPTIONS["RCSB PDB"])
    return deepcopy(items)


def pubchem_citations(publication_ids):
    """PubMed pointers remain incomplete citations, never DOI/name enriched."""
    from .snapshot import canonical_json, digest

    citations, gaps = [], []
    for pubmed in publication_ids:
        # A source-stated pointer cannot overwrite a fuller citation already used
        # by the host under its publication identifier.
        identifier = "sabueso:pubchem-primary-citation:" + digest(
            canonical_json({"pubmed_id": pubmed})
        )
        citations.append(
            {
                "id": identifier,
                "type": "article",
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pubmed}/",
            }
        )
        gaps.append(
            {
                "publication_ref": "pubmed:" + pubmed,
                "citation_id": identifier,
                "reason": "measurement_citation_metadata_not_stated",
                "fields": ["title", "authors", "year"],
            }
        )
    return citations, gaps


def bindingdb_citations(publications):
    """Retain native DOI/PubMed forms without replacing fuller host citations."""
    from .snapshot import canonical_json, digest

    citations, gaps = [], []
    for publication in publications:
        identifier = "sabueso:bindingdb-primary-citation:" + digest(
            canonical_json(publication)
        )
        item = {"id": identifier, "type": "article"}
        if publication.get("doi"):
            item.update(
                doi=deepcopy(publication["doi"]),
                url="https://doi.org/" + str(publication["doi"]),
            )
        elif publication.get("pmid"):
            item["url"] = f"https://pubmed.ncbi.nlm.nih.gov/{publication['pmid']}/"
        citations.append(item)
        gaps.append(
            {
                "publication": deepcopy(publication),
                "citation_id": identifier,
                "reason": "measurement_citation_metadata_not_stated",
                "fields": ["title", "authors", "year"],
            }
        )
    return citations, gaps


def chembl_citations(documents):
    """Original document forms remain distinct; missing authors are never inferred."""
    from .snapshot import canonical_json, digest

    citations, gaps = [], []
    for document_id, document in sorted(documents.items()):
        identifier = "sabueso:chembl-document-citation:" + digest(
            canonical_json(document)
        )
        item = {"id": identifier, "type": "article"}
        for key in ("title", "year", "journal", "doi"):
            if document.get(key):
                item[key] = deepcopy(document[key])
        if document.get("doi"):
            item["url"] = "https://doi.org/" + document["doi"]
        elif document.get("pubmed_id"):
            item["url"] = f"https://pubmed.ncbi.nlm.nih.gov/{document['pubmed_id']}/"
        gaps.append(
            {
                "document_id": document_id,
                "citation_id": identifier,
                "reason": "document_citation_metadata_not_stated",
                "fields": [
                    key for key in ("title", "authors", "year") if not item.get(key)
                ],
            }
        )
        citations.append(item)
    return citations, gaps


def structure_citations(entries):
    """Preserve only primary publication metadata stated for received PDB entries.

    No DOI lookup supplies missing authors, title or date. Identical metadata is
    reused; different source-stated forms of a publication remain distinct. This
    prevents a partial citation from replacing a previous complete reference.
    """
    from .snapshot import canonical_json, digest

    citations, gaps = {}, []
    for entry in entries:
        if entry["outcome"] not in {"received", "partial"}:
            continue
        citation = entry.get("primary_citation") or {}
        if not citation:
            gaps.append(
                {"pdb_id": entry["pdb_id"], "reason": "primary_citation_not_stated"}
            )
            continue
        doi = citation.get("pdbx_database_id_DOI")
        pubmed = citation.get("pdbx_database_id_PubMed")
        identifier = "sabueso:rcsb-primary-citation:" + digest(canonical_json(citation))
        item = {"id": identifier, "type": "article"}
        for source_key, target_key in (
            ("title", "title"),
            ("rcsb_authors", "authors"),
            ("year", "year"),
            ("journal_abbrev", "journal"),
            ("pdbx_database_id_DOI", "doi"),
        ):
            if citation.get(source_key):
                item[target_key] = deepcopy(citation[source_key])
        if doi:
            item["url"] = "https://doi.org/" + doi
        elif pubmed:
            item["url"] = f"https://pubmed.ncbi.nlm.nih.gov/{pubmed}/"
        missing = [key for key in ("title", "authors", "year") if not item.get(key)]
        if missing:
            gaps.append(
                {
                    "pdb_id": entry["pdb_id"],
                    "citation_id": identifier,
                    "reason": "primary_citation_metadata_not_stated",
                    "fields": missing,
                }
            )
        citations[identifier] = item
    return list(citations.values()), gaps


def software():
    from sabueso import __version__

    return {
        "id": f"software:sabueso:{__version__}",
        "type": "software",
        "title": "Sabueso",
        "authors": ["Prada-Gracia, Diego", "Moreno-Vargas, Liliana M."],
        "version": __version__,
        # The concept DOI describes the project. Do not label an unreleased
        # checkout with the version-specific DOI of its preceding release.
        "doi": "10.5281/zenodo.22937375",
        "url": "https://github.com/uibcdf/sabueso",
    }
