# Literature Index

Local folder: `literature-survey/papers`

For the newer source-by-source collection added after the initial architecture references, see `RECENT_PAPERS_INDEX.md`.

## Folder Structure

| Folder | Meaning | Current status |
|---|---|---|
| `papers/Standards` | 3GPP, ETSI, O-RAN PAS, ITU-T-style primary standards and technical reports | Contains current architecture/security/ZSM references. |
| `papers/arXiv` | Academic preprints downloaded from arXiv | Contains current survey/security preprints. |
| `papers/Government-Reports` | Government, regulator, public-sector security or policy reports | Contains current BSI 5G RAN risk report. |
| `papers/IEEE` | IEEE peer-reviewed papers | Empty; reserved for next literature collection pass. |
| `papers/Elsevier` | Elsevier / ScienceDirect papers | Empty; reserved for next literature collection pass. |
| `papers/Springer` | Springer / SpringerLink papers | Empty; reserved for next literature collection pass. |
| `papers/ACM` | ACM Digital Library papers | Empty; reserved for next literature collection pass. |

| File | Source URL | Use in project |
|---|---|---|
| `papers/Standards/ETSI_TS_103982_O-RAN_Architecture_Description_v08.pdf` | https://www.etsi.org/deliver/etsi_ts/103900_103999/103982/08.00.00_60/ts_103982v080000p.pdf | Baseline O-RAN architecture, SMO, RIC, O-CU/O-DU/O-RU, open interfaces. |
| `papers/Standards/ETSI_TS_123501_5GS_System_Architecture_R16.pdf` | https://www.etsi.org/deliver/etsi_ts/123500_123599/123501/16.10.00_60/ts_123501v161000p.pdf | 5G system architecture, core network functions, N1/N2/N3/N4/N6, slicing. |
| `papers/Standards/ETSI_TS_138401_NG-RAN_Architecture_R18.pdf` | https://www.etsi.org/deliver/etsi_ts/138400_138499/138401/18.01.00_60/ts_138401v180100p.pdf | NG-RAN architecture, gNB, CU/DU split, NG, Xn, F1. |
| `papers/Standards/ETSI_TS_133501_5G_Security_R16.pdf` | https://www.etsi.org/deliver/etsi_ts/133500_133599/133501/16.11.00_60/ts_133501v161100p.pdf | 5G authentication, NAS/AS security, subscriber privacy, SBA security. |
| `papers/Standards/ETSI_GR_ZSM_015_Digital_Twin_Networks.pdf` | https://www.etsi.org/deliver/etsi_gr/ZSM/001_099/015/01.01.01_60/gr_ZSM015v010101p.pdf | Digital twin network concepts for zero-touch/autonomous network management. |
| `papers/Government-Reports/BSI_5G_RAN_Risk_Analysis.pdf` | https://www.bsi.bund.de/SharedDocs/Downloads/EN/BSI/Publications/Studies/5G/5G_RAN.pdf?__blob=publicationFile&v=3 | Threat/risk view for 5G RAN and interfaces. Useful for security section. |
| `papers/arXiv/Polese_2022_Understanding_ORAN_Architecture_Interfaces_Security.pdf` | https://arxiv.org/pdf/2202.01032 | Academic O-RAN survey covering architecture, interfaces, algorithms, security, and research challenges. |
| `papers/arXiv/Zero_Touch_Networks_Next_Generation_Automation.pdf` | https://arxiv.org/pdf/2312.04159 | Academic survey on zero-touch networks and AI-driven automation. |
| `papers/arXiv/ZT_RIC_Zero_Trust_RIC_Framework.pdf` | https://arxiv.org/pdf/2411.07128 | Security-focused paper for RIC/xApp privacy, confidentiality, and zero-trust design ideas. |

## Suggested Reading Order

1. `papers/Standards/ETSI_TS_123501_5GS_System_Architecture_R16.pdf`
2. `papers/Standards/ETSI_TS_138401_NG-RAN_Architecture_R18.pdf`
3. `papers/Standards/ETSI_TS_103982_O-RAN_Architecture_Description_v08.pdf`
4. `papers/arXiv/Polese_2022_Understanding_ORAN_Architecture_Interfaces_Security.pdf`
5. `papers/Standards/ETSI_GR_ZSM_015_Digital_Twin_Networks.pdf`
6. `papers/arXiv/Zero_Touch_Networks_Next_Generation_Automation.pdf`
7. `papers/Standards/ETSI_TS_133501_5G_Security_R16.pdf`
8. `papers/Government-Reports/BSI_5G_RAN_Risk_Analysis.pdf`
9. `papers/arXiv/ZT_RIC_Zero_Trust_RIC_Framework.pdf`

## Literature Survey Themes to Extract

| Theme | Questions to answer |
|---|---|
| O-RAN architecture | What control loops exist? Which functions are disaggregated? Which interfaces are open? |
| 5G architecture | Which functions carry control plane vs user plane? Where do sessions, mobility, policy, and slicing live? |
| Digital twin network | What is represented in the twin? What is simulated? How does the twin stay synchronized with the real network? |
| AI-native networking | Which decisions can be learned? Which should remain rules/policy based? How is model drift managed? |
| Security | What new attack surfaces are introduced by open interfaces, xApps, rApps, and cloud-native RAN? |
| NOC operations | How can telemetry, incidents, RCA, prediction, and closed-loop healing be turned into a marketable assurance platform? |
