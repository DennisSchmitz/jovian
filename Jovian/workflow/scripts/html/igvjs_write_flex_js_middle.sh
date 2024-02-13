# shellcheck shell=bash
# This script (part 3) this script writes the flexible part of the required JavaScript
# this script should be called for every sample.

INPUT="$1"
OUTPUT_HTML="$2"
INPUT_REF_FASTA="$3"
INPUT_REF_GC_BEDGRAPH="$4"
INPUT_REF_ZIPPED_ORF_GFF="$5"
INPUT_ZIPPED_SNP_VCF="$6"
INPUT_SORTED_BAM="$7"
NGINX_IP="$8"
NGINX_PORT="$9"


SAMPLE="sample_${INPUT//-/_}"

cat << EOF >> ${OUTPUT_HTML}
        ${SAMPLE} = document.getElementById("${SAMPLE}");
        options =
            {
                reference:
                {
                    id: "${INPUT}",
                    fastaURL: "${NGINX_IP}:${NGINX_PORT}/${INPUT_REF_FASTA}",
                    wholeGenomeView: false,
                    tracks: [
                        {
                            type: "wig",
                            name: "GC contents",
                            format: "bedGraph",
                            url: "${NGINX_IP}:${NGINX_PORT}/${INPUT_REF_GC_BEDGRAPH}",
                            min: "0",
                            max: "1",
                            order: Number.MAX_VALUE
                        },
                        {
                            name:"SNPs",
                            type:"variant",
                            format:"vcf",
                            url: "${NGINX_IP}:${NGINX_PORT}/${INPUT_ZIPPED_SNP_VCF}",
                            indexURL: "${NGINX_IP}:${NGINX_PORT}/${INPUT_ZIPPED_SNP_VCF}.tbi",
                            displayMode: "SQUISHED",
                            order: 2
                        },
                        {
                            type: "alignment",
                            format: "bam",
                            colorBy: "strand",
                            url: "${NGINX_IP}:${NGINX_PORT}/${INPUT_SORTED_BAM}",
                            indexURL: "${NGINX_IP}:${NGINX_PORT}/${INPUT_SORTED_BAM}.bai",
                            indexed: "true",
                            name: "Alignment",
                            showSoftClips: false,
                            viewAsPairs: true,
                            order: 3
                        },
                        {
                            type: "annotation",
                            name: "ORF predictions",
                            format: "gff3",
                            url: "${NGINX_IP}:${NGINX_PORT}/${INPUT_REF_ZIPPED_ORF_GFF}",
                            indexURL: "${NGINX_IP}:${NGINX_PORT}/${INPUT_REF_ZIPPED_ORF_GFF}.tbi",
                            displayMode: "EXPANDED",
                            order: 1
                        }
                    ]
                },
            };
        igv.createBrowser(${SAMPLE}, options);
EOF
