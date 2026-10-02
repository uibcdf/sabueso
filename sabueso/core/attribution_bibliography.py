"""Offline resource descriptions, verified 2026-10-02; never DOI-enriched.

These works describe resources, not the experimental findings in their entries.
Metadata sources are recorded in docs/content/user/attribution.md.
"""

from copy import deepcopy

_DESCRIPTIONS = {
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
}


def descriptions(source):
    item = _DESCRIPTIONS.get(source)
    return [deepcopy(item)] if item else []


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
