"""gnomAD: population frequencies of protein changes (``annotations.population_variants``)."""

from __future__ import annotations

from sabueso.enrichers import Enricher, NothingToAsk, Request

#: Every protein-level variant, up to a safety ceiling; a cut is reported.
DEFAULT_LIMIT = 5000


class GnomAD(Enricher):
    option = "gnomad"
    source = "gnomAD"
    registry_id = "gnomad"
    areas = ("annotations.population_variants",)
    organisms = (9606,)
    coverage_detail = "gnomAD covers human variants only"
    option_kind = "options"

    @property
    def match(self):
        # The pext records of the same source carry data "pext" (#102).
        return {"source": self.source, "data": None}

    def client(self):
        from sabueso.tools.db.gnomad import OnlineGnomADClient

        return OnlineGnomADClient()

    def requests(self, context, options):
        genes = sorted(
            {v.split(".")[0] for v, _ in context.xref_properties("Ensembl", "GeneId")}
        )
        if not genes:
            raise NothingToAsk("the entry cross-references no Ensembl gene")
        canonical = context.transcripts["canonical"]
        # Transcripts UniProt states for its other isoforms: a change on one of them
        # would be placed through the isoform map (#102).
        isoform_transcripts = sorted(
            t for t in context.transcripts["isoform_of"] if t.startswith("ENST")
        )
        requests = []
        for gene in genes:
            # The Ensembl transcripts UniProt states encode its canonical isoform.
            transcripts = sorted(
                {
                    x["id"].split(".")[0]
                    for x in context.xrefs("Ensembl")
                    if x["id"].split(".")[0] in canonical
                    and any(
                        p.get("key") == "GeneId"
                        and str(p.get("value")).split(".")[0] == gene
                        for p in x.get("properties") or []
                    )
                }
            )
            requests.append(
                Request(
                    gene,
                    {"source": self.source, "identifier": gene},
                    {
                        "canonical_transcripts": transcripts,
                        "isoform_transcripts": isoform_transcripts,
                    },
                )
            )
        return requests

    def fetch(self, client, request, options):
        from sabueso.core.errors import RecordNotFoundError

        response = client.variants(request.identifier)
        # Only the canonical transcripts gnomAD annotates: UniProt may cross-reference
        # newer Ensembl transcripts than the dataset's GENCODE release (ENO1: 17, of
        # which gnomAD knows one), and each would cost a request.
        annotated = {
            t.get("transcript_id")
            for t in response["record"]["gene"].get("transcripts") or []
        }
        on_canonical = {}
        for transcript in request.args["canonical_transcripts"]:
            if transcript not in annotated:
                on_canonical[transcript] = "not_in_dataset"
                continue
            try:
                on_canonical[transcript] = client.transcript_variants(transcript)
            except RecordNotFoundError:
                on_canonical[transcript] = None
        # A change gnomAD ranks on another isoform's transcript, and states no protein
        # change for on the canonical one in the transcript query, would be placed
        # through UniProt's isoform map. Its DNA may lie in an exon the canonical
        # transcript lacks (PKM's M1 exon), so gnomAD is asked what it is there (#102).
        stated = {
            v["variant_id"]
            for answer in on_canonical.values()
            if isinstance(answer, dict)
            for v in answer["record"]["variants"]
        }
        isoform = set(request.args.get("isoform_transcripts") or ())
        candidates = sorted(
            v["variant_id"]
            for v in response["record"]["variants"]
            if v.get("hgvsp")
            and v.get("transcript_id") in isoform
            and v["variant_id"] not in stated
        )
        consequences = client.consequences(candidates)["record"] if candidates else {}
        return {
            **response,
            "on_canonical": on_canonical,
            "consequences": consequences,
            "checked": len(candidates),
        }

    def map(self, context, request, response, options):
        from sabueso.mappings.gnomad import map_variants, merged

        limit = options.get("limit", DEFAULT_LIMIT)
        on_canonical = response.get("on_canonical") or {}
        asked = {t for t, a in on_canonical.items() if isinstance(a, dict)}
        variants, without = merged(
            response["record"]["variants"],
            [
                answer["record"]
                for _, answer in sorted(on_canonical.items())
                if isinstance(answer, dict)
            ],
            response.get("consequences") or {},
            asked,
        )
        mapped = map_variants(
            variants[:limit],
            context.anchor,
            context.transcripts,
            response.get("retrieved_at", ""),
            response.get("version"),
        )
        return mapped, {
            "status": "added" if variants else "not_found",
            "version": response.get("version"),
            "count": len(mapped["source_assertions"]),
            "without_protein_change": without,
            "truncated": len(variants) > limit,
            "total_count": len(variants),
            "canonical_transcripts": [
                _asked(transcript, answer)
                for transcript, answer in sorted(on_canonical.items())
            ],
            "consequences_checked": response.get("checked", 0),
        }


def _asked(transcript, answer):
    """What was asked for a canonical transcript: its version, or why it has none."""
    if answer == "not_in_dataset":
        return {"transcript": transcript, "not_in_dataset": True}
    if answer is None:
        return {"transcript": transcript, "not_found": True}
    return {
        "transcript": transcript,
        "version": answer["record"]["transcript"].get("transcript_version"),
    }


class GnomADPext(Enricher):
    """gnomAD's pext: how much of a gene's expression in each GTEx tissue includes each
    coding region (``annotations.exon_usage_by_tissue``, #102)."""

    option = "exon_usage"
    source = "gnomAD"
    data = "pext"
    registry_id = "gnomad"
    client_option = "gnomad_client"
    areas = ("annotations.exon_usage_by_tissue", "annotations.isoform_coding_exons")
    organisms = (9606,)
    coverage_detail = "gnomAD's pext covers human genes only"

    @property
    def match(self):
        return {"source": self.source, "data": self.data}

    def client(self):
        from sabueso.tools.db.gnomad import OnlineGnomADClient

        return OnlineGnomADClient()

    def record(self, context, options):
        return {"source": self.source, "data": self.data, "identifier": context.anchor}

    def requests(self, context, options):
        genes = sorted(
            {v.split(".")[0] for v, _ in context.xref_properties("Ensembl", "GeneId")}
        )
        if not genes:
            raise NothingToAsk("the entry cross-references no Ensembl gene")
        return [
            Request(g, {"source": self.source, "data": self.data, "identifier": g})
            for g in genes
        ]

    def fetch(self, client, request, options):
        return client.pext(request.identifier)

    def map(self, context, request, response, options):
        from sabueso.mappings.gnomad import map_isoform_exons, map_pext

        mapped = map_pext(
            response["record"],
            context.anchor,
            response.get("retrieved_at", ""),
            response.get("version"),
        )
        isoform_of = _isoforms_of_transcripts(context)
        exons = map_isoform_exons(
            response["record"],
            isoform_of,
            context.anchor,
            response.get("retrieved_at", ""),
            response.get("version"),
        )
        for key in ("fields", "field_source_assertions"):
            mapped[key].update(exons[key])
        mapped["source_assertions"].extend(exons["source_assertions"])
        listed = {i["transcript"] for i in exons["fields"].get(EXONS, [])}
        return mapped, {
            "status": "added",
            "version": response.get("version"),
            "count": len(mapped["fields"].get(PEXT_FIELD, [])),
            "flags": (response["record"].get("pext") or {}).get("flags") or [],
            "isoform_transcripts": len(listed),
            "isoform_transcripts_not_in_dataset": len(set(isoform_of) - listed),
        }


# The field, not the enricher (PEXT below): the record counted nothing until 0.9.0.
PEXT_FIELD = "annotations.exon_usage_by_tissue"
EXONS = "annotations.isoform_coding_exons"


def _isoforms_of_transcripts(context):
    """Ensembl transcript → the UniProt isoform the entry's cross-reference states it
    encodes; in an entry without isoforms, the entry itself."""
    described = any(
        comment.get("commentType") == "ALTERNATIVE PRODUCTS" and comment.get("isoforms")
        for comment in context.entry.get("comments") or []
    )
    out = {}
    for xref in context.xrefs("Ensembl"):
        transcript = str(xref.get("id", "")).split(".")[0]
        isoform = xref.get("isoformId")
        if isoform is None and not described:
            isoform = context.anchor
        if transcript and isoform:
            out[transcript] = isoform
    return out


ENRICHER = GnomAD()
PEXT = GnomADPext()
