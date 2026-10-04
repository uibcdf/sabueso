"""Offline resource descriptions, verified 2026-10-02/04; never DOI-enriched.

These works describe resources, not the experimental findings in their entries.
Metadata sources are recorded in docs/content/user/attribution.md.
"""

from copy import deepcopy

_DESCRIPTIONS = {
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
    item = _DESCRIPTIONS.get(source)
    return [deepcopy(item)] if item else []


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
