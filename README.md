# ForEXy
Utility codes for the EXFOR Library

## Requirements
* pylatexenc
* pyspellchecker
* requests

## Input files
The following input files are available on the ForEXy zipped file on the [NRDC Software website](https://nds.iaea.org/nrdc/nrdc_sft/):
* JSON dictionary (e.g., dict_9133.json)
* Supplemental dictionary file for DIC227 (e.g., dict_arc_sup.227)
* CSS file for J4VIEW and X4VIEW (e.g., exfor.css)
* CINDA code list for CODUSE (e.g., x4_coduse.cin)
* Technical term dictionary for SPELLS (e.g., x4_spells.dic)

## Installation
```
pip install forexy
```

## Modules 

Module | Purpose
---    | ---
CODDIC | Analyse use of codes in J4 library.
DIC227 | Produce Archive Dictionary 227 from a NUBASE file.
DICA2J | Convert Archive dictionaries to a JSON Dictionary.
DICDIS | Prepare Archive and Backup dictionaries for distribution.
DICJ2A | Convert a JSON Dictionary to Archive dictionaries.
DICJ2T | Convert a JSON Dictionary to a Transmission dictionary.
DIRINI | Split an EXFOR library tape into EXFOR entry files.
DIRUPD | Update the EXFOR entry files with an EXFOR transmission tape.
EXTMUL | Extraction of a dataset from a multiple reaction formalism subentry.
J4TOX4 | Convert a J4 file to an EXFOR file.
J4VIEW | Convert a J4 file to an HTML file.
MAKCOV | Produce a data table and covariance matrix from a J4 file.
MAKJ4L | Produce and update J4 library.
MAKLIB | Merge EXFOR entry files into a single library tape.
POIPOI | Remove pointers from a J4 file.
REFBIB | Extract bibliography of reference by using DOI.
REFDOI | Obtain DOI for articles registered in CrossRef.
SEQADD | Add record identification to an EXFOR file.
SPELLS | Check English spell in free text in EXFOR format.
X4TOJ4 | Convert an EXFOR file to a J4 file.
X4VIEW | Convert an EXFOR file to an HTML file.


## References
* Naohiko Otuka, Vidya Devi, Osamu Iwamoto, "EXFOR utility codes (ForEXy) and their application to neutron fission cross section evaluation", [Appl.Radiat.Isot.225(2025)111903](https://doi.org/10.1016/j.apradiso.2025.111903) / [arXiv] ( 	
https://doi.org/10.48550/arXiv.2505.03758).
* Naohiko Otuka, "ForEXy: Utility Codes for EXFOR Library", Report [IAEA-NDS-0244](https://doi.org/10.61092/iaea.hz1z-0dx3), International Atomic Energy Agency, 2025.
