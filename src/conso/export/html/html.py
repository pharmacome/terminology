# -*- coding: utf-8 -*-

"""Export the Curation of Neurodegeneration Supporting Ontology (CONSO) to HTML."""

import os
from collections import defaultdict
from typing import Optional

import pandas as pd
from jinja2 import Environment, FileSystemLoader

#: Path to this directory
HERE = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.join(HERE, os.pardir, os.pardir, os.pardir, os.pardir)

CLASSES_PATH = os.path.abspath(os.path.join(ROOT, 'classes.tsv'))
TERMS_PATH = os.path.abspath(os.path.join(ROOT, 'terms.tsv'))
SYNONYMS_PATH = os.path.abspath(os.path.join(ROOT, 'synonyms.tsv'))
XREFS_PATH = os.path.abspath(os.path.join(ROOT, 'xrefs.tsv'))
RELATIONS_PATH = os.path.abspath(os.path.join(ROOT, 'relations.tsv'))

OUTPUT_DIRECTORY = os.path.join(ROOT, 'docs')

environment = Environment(autoescape=True, loader=FileSystemLoader(HERE), trim_blocks=False)
index_template = environment.get_template('index.html')
term_template = environment.get_template('term.html')


def main(directory: Optional[str] = None, debug_links: bool = False) -> None:
    """Export CONSO as HTML.

    :param directory: The output directory where the html goes.
    :param debug_links: If true, uses links directly to index files instead of by folder.
    """
    terms_df = pd.read_csv(TERMS_PATH, sep='\t')
    terms_df = terms_df[terms_df.Name != 'WITHDRAWN']

    synonyms = defaultdict(list)
    for _, row in pd.read_csv(SYNONYMS_PATH, sep='\t').iterrows():
        synonyms[row.Identifier].append((row.Synonym, row.Reference, row.Specificity))

    xrefs = defaultdict(list)
    for _, row in pd.read_csv(XREFS_PATH, sep='\t').iterrows():
        xrefs[row.identifier].append((row.database, row.database_identifier))

    incoming_relations = defaultdict(list)
    outgoing_relations = defaultdict(list)
    for _, row in pd.read_csv(RELATIONS_PATH, sep='\t').iterrows():
        if row['Source Namespace'] == 'HBP':
            outgoing_relations[row['Source Identifier']].append((
                row['Relation'],
                row['Target Namespace'],
                row['Target Identifier'],
                row['Target Name'],
            ))
        if row['Target Namespace'] == 'HBP':
            incoming_relations[row['Target Identifier']].append((
                row['Source Namespace'],
                row['Source Identifier'],
                row['Source Name'],
                row['Relation'],
            ))

    if directory is None:
        directory = OUTPUT_DIRECTORY

    os.makedirs(directory, exist_ok=True)

    index_html = index_template.render(
        terms_df=terms_df,
        incoming_relations=incoming_relations,
        outgoing_relations=outgoing_relations,
        synonyms=synonyms,
        xrefs=xrefs,
        debug_links=debug_links,
    )
    with open(os.path.join(directory, 'index.html'), 'w') as file:
        print(index_html, file=file)

    for _, row in terms_df.iterrows():
        subdirectory = os.path.join(directory, row.Identifier)
        os.makedirs(subdirectory, exist_ok=True)
        html = term_template.render(
            row=row,
            synonyms=synonyms[row.Identifier],
            xrefs=xrefs[row.Identifier],
            incoming_relations=incoming_relations[row.Identifier],
            outgoing_relations=outgoing_relations[row.Identifier],
            debug_links=debug_links,
        )
        with open(os.path.join(subdirectory, 'index.html'), 'w') as file:
            print(html, file=file)


if __name__ == '__main__':
    main()
