## GO analysis using GOATools
import functools
import pandas as pd
import collections as cx
from pybiomart import Dataset
# GO analysis
from goatools.base import download_go_basic_obo
from goatools.base import download_ncbi_associations
from goatools.obo_parser import GODag
from goatools.anno.genetogo_reader import Gene2GoReader
from goatools.goea.go_enrichment_ns import GOEnrichmentStudyNS

@functools.lru_cache()
def get_database():
    dataset = Dataset(name="hsapiens_gene_ensembl",
                      host="http://www.ensembl.org",
                      use_cache=True)
    db = dataset.query(attributes=["ensembl_gene_id",
                                   "external_gene_name",
                                   "entrezgene_id"],
                       use_attr_names=True).dropna(subset=['entrezgene_id'])
    return db


@functools.lru_cache()
def get_twas():
    df = pd.read_csv('../../_m/fusion_associations.txt', sep='\t')
    return df[(df["FDR"] < 0.05)]


@functools.lru_cache()
def convert2entrez():
    if 'EntrezID' in get_twas().columns:
        return get_twas().rename(columns={'EntrezID': 'entrezgene_id'})
    else:
        return get_twas().merge(get_database(), left_on='FILE',
                                right_on='ensembl_gene_id')


@functools.lru_cache()
def get_upregulated():
    return convert2entrez().loc[(convert2entrez()['TWAS.Z'] > 0)]


@functools.lru_cache()
def get_downregulated():
    return convert2entrez().loc[(convert2entrez()['TWAS.Z'] < 0)]


def obo_annotation(alpha=0.05):
    # database annotation
    fn_obo = download_go_basic_obo()
    fn_gene2go = download_ncbi_associations() # must be gunzip to work
    obodag = GODag(fn_obo) # downloads most up-to-date
    anno_hs = Gene2GoReader(fn_gene2go, taxids=[9606])
    # get associations
    ns2assoc = anno_hs.get_ns2assc()
    for nspc, id2gos in ns2assoc.items():
        print("{NS} {N:,} annotated human genes".format(NS=nspc, N=len(id2gos)))
    goeaobj = GOEnrichmentStudyNS(
        get_database()['entrezgene_id'], # List of human genes with entrez IDs
        ns2assoc, # geneid/GO associations
        obodag, # Ontologies
        propagate_counts = False,
        alpha = alpha, # default significance cut-off
        methods = ['fdr_bh'])
    return goeaobj


def run_goea(direction):
    if direction == "Up":
        df = get_upregulated()
    elif direction == "Down":
        df = get_downregulated()
    else:
        df = convert2entrez()
    geneids_study = {z[0]:z[1] for z in zip(df['entrezgene_id'], df['ID'])}
    goeaobj = obo_annotation()
    goea_results_all = goeaobj.run_study(geneids_study)
    goea_results_sig = [r for r in goea_results_all if r.p_fdr_bh < 0.05]
    ctr = cx.Counter([r.NS for r in goea_results_sig])
    print('Significant results[{TOTAL}] = {BP} BP + {MF} MF + {CC} CC'.format(
        TOTAL=len(goea_results_sig),
        BP=ctr['BP'],  # biological_process
        MF=ctr['MF'],  # molecular_function
        CC=ctr['CC'])) # cellular_component
    if direction == "Up":
        label = "upregulated"
    elif direction == "Down":
        label = "downregulated"
    else:
        label = "all_TWAS"
    goeaobj.wr_xlsx("GO_analysis_%s.xlsx" % label, goea_results_sig)
    goeaobj.wr_txt("GO_analysis_%s.txt" % label, goea_results_sig)


def main():
    for direction in ["All", "Up", "Down"]:
        print(direction)
        run_goea(direction)


if __name__ == '__main__':
    main()
