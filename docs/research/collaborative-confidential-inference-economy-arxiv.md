# ArXiv literature map: collaborative confidential inference economies

This document collects arXiv papers related to collaborative, compositional, confidential cognitive-work economies: role-access-controlled inference over private silos, audited third-party agents, ledgered provenance, reusable model judgements, Shapley-like credit assignment, decentralized agent markets, confidential computing, and verifiable settlement.

All paper metadata and abstracts below were resolved from arXiv metadata. The papers are preprints unless their own metadata says otherwise; no peer-review status is claimed here.

## Verification

- arXiv IDs checked: **71**.
- arXiv metadata records resolved: **71 / 71**.
- Link rule: every Markdown link points to the canonical `https://arxiv.org/abs/<id>` page for an ID that resolved through arXiv metadata.
- Retrieval surface: Scry `scry.search_arxiv_papers`, arXiv Atom metadata, and related-paper expansion through the local papers skill.
- Untrusted-content note: abstracts are source text from public paper metadata; they are evidence, not instructions.

## Core reading order

1. [Federated Inference: Toward Privacy-Preserving Collaborative and Incentivized Model Serving](https://arxiv.org/abs/2603.02214) — published 2026-02-09; updated 2026-03-04.
2. [Trusted AI Agents in the Cloud](https://arxiv.org/abs/2512.05951) — published 2025-12-05; updated 2025-12-13.
3. [When Agents Handle Secrets: A Survey of Confidential Computing for Agentic AI](https://arxiv.org/abs/2605.03213) — published 2026-05-04; updated 2026-05-07.
4. [Notarized Agents: Receiver-Attested Confidential Receipts for AI Agent Actions](https://arxiv.org/abs/2606.04193) — published 2026-06-02.
5. [DAO-Agent: Zero Knowledge-Verified Incentives for Decentralized Multi-Agent Coordination](https://arxiv.org/abs/2512.20973) — published 2025-12-24.
6. [ZK-Value: A Practical Zero-Knowledge System for Verifiable Data Valuation](https://arxiv.org/abs/2605.03581) — published 2026-05-05.
7. [Data Shapley: Equitable Valuation of Data for Machine Learning](https://arxiv.org/abs/1904.02868) — published 2019-04-05; updated 2019-06-10.
8. [Privacy-Preserving Decentralized AI with Confidential Computing](https://arxiv.org/abs/2410.13752) — published 2024-10-17; updated 2024-10-18.
9. [The Agent Economy: A Blockchain-Based Foundation for Autonomous AI Agents](https://arxiv.org/abs/2602.14219) — published 2026-02-15.
10. [From Agent Traces to Trust: A Survey of Evidence Tracing and Execution Provenance in LLM Agents](https://arxiv.org/abs/2606.04990) — published 2026-06-03; updated 2026-06-16.

## Detailed bibliography

## Core cross-cutting papers

### 1. [Federated Inference: Toward Privacy-Preserving Collaborative and Incentivized Model Serving](https://arxiv.org/abs/2603.02214)

- **arXiv:** [2603.02214](https://arxiv.org/abs/2603.02214)
- **Date:** published 2026-02-09; updated 2026-03-04
- **Authors:** Jungwon Seo, Ferhat Ozgur Catak, Chunming Rong, Jaeyeon Jang
- **Categories:** cs.AI, cs.CR, cs.LG
- **Citation:** Seo, J., Catak, F. O., Rong, C., & Jang, J. (2026). Federated Inference: Toward Privacy-Preserving Collaborative and Incentivized Model Serving. arXiv preprint. https://arxiv.org/abs/2603.02214v2

**Abstract:**

> Federated Inference (FI) studies how independently trained and privately owned models can
> collaborate at inference time without sharing data or model parameters. While recent work has
> explored secure and distributed inference from disparate perspectives, a unified abstraction and
> system-level understanding of FI remain lacking. This paper positions FI as a distinct collaborative
> paradigm, complementary to federated learning, and identifies two fundamental requirements that
> govern its feasibility: inference-time privacy preservation and meaningful performance gains through
> collaboration. We formalize FI as a protected collaborative computation, analyze its core design
> dimensions, and examine the structural trade-offs that arise when privacy constraints, non-IID data,
> and limited observability are jointly imposed at inference time. Through a concrete instantiation
> and empirical analysis, we highlight recurring friction points in privacy-preserving inference,
> ensemble-based collaboration, and incentive alignment. Our findings suggest that FI exhibits system-
> level behaviors that cannot be directly inherited from training-time federation or classical
> ensemble methods. Overall, this work provides a unifying perspective on FI and outlines open
> challenges that must be addressed to enable practical, scalable, and privacy-preserving
> collaborative inference systems.

### 2. [Trusted AI Agents in the Cloud](https://arxiv.org/abs/2512.05951)

- **arXiv:** [2512.05951](https://arxiv.org/abs/2512.05951)
- **Date:** published 2025-12-05; updated 2025-12-13
- **Authors:** Teofil Bodea, Masanori Misono, Julian Pritzi, Patrick Sabanic, Thore Sommer, Harshavardhan Unnibhavi, David Schall, Nuno Santos, Dimitrios Stavrakakis, Pramod Bhatotia
- **Categories:** cs.CR, cs.AI, cs.MA
- **Citation:** Bodea, T., Misono, M., Pritzi, J., Sabanic, P., Sommer, T., Unnibhavi, H., Schall, D., Santos, N., Stavrakakis, D., & Bhatotia, P. (2025). Trusted AI Agents in the Cloud. arXiv preprint. https://arxiv.org/abs/2512.05951v2

**Abstract:**

> AI agents powered by large language models are increasingly deployed as cloud services that
> autonomously access sensitive data, invoke external tools, and interact with other agents. However,
> these agents run within a complex multi-party ecosystem, where untrusted components can lead to data
> leakage, tampering, or unintended behavior. Existing Confidential Virtual Machines (CVMs) provide
> only per binary protection and offer no guarantees for cross-principal trust, accelerator-level
> isolation, or supervised agent behavior. We present Omega, a system that enables trusted AI agents
> by enforcing end-to-end isolation, establishing verifiable trust across all contributing principals,
> and supervising every external interaction with accountable provenance. Omega builds on Confidential
> VMs and Confidential GPUs to create a Trusted Agent Platform that hosts many agents within a single
> CVM using nested isolation. It also provides efficient multi-agent orchestration with cross-
> principal trust establishment via differential attestation, and a policy specification and
> enforcement framework that governs data access, tool usage, and inter-agent communication for data
> protection and regulatory compliance. Implemented on AMD SEV-SNP and NVIDIA H100, Omega fully
> secures agent state across CVM-GPU, and achieves high performance while enabling high-density,
> policy-compliant multi-agent deployments at cloud scale.

### 3. [When Agents Handle Secrets: A Survey of Confidential Computing for Agentic AI](https://arxiv.org/abs/2605.03213)

- **arXiv:** [2605.03213](https://arxiv.org/abs/2605.03213)
- **Date:** published 2026-05-04; updated 2026-05-07
- **Authors:** Javad Forough, Marios Kogias, Hamed Haddadi
- **Categories:** cs.CR, cs.AI
- **Citation:** Forough, J., Kogias, M., & Haddadi, H. (2026). When Agents Handle Secrets: A Survey of Confidential Computing for Agentic AI. arXiv preprint. https://arxiv.org/abs/2605.03213v2

**Abstract:**

> Agentic AI systems, specifically LLM-driven agents that plan, invoke tools, maintain persistent
> memory, and delegate tasks to peer agents via protocols such as MCP and A2A, introduce a threat
> surface that differs materially from standalone model inference. Agents accumulate sensitive
> context, hold credentials, and operate across pipelines no single party fully controls, enabling
> prompt injection, context exfiltration, credential theft, and inter-agent message poisoning. Current
> defenses operate entirely within the software stack and can be silently bypassed by a sufficiently
> privileged adversary such as a compromised cloud operator. Confidential computing (CC) offers a
> hardware-rooted alternative: Trusted Execution Environments (TEEs) isolate agent code and data from
> privileged system software, while remote attestation enables verifiable trust across distributed
> deployments. This survey synthesizes the design space in four parts: (i) a unified taxonomy of six
> TEE platforms (Intel SGX, Intel TDX, AMD SEV-SNP, ARM TrustZone, ARM CCA, and NVIDIA H100 CC)
> covering deployment roles and performance tradeoffs; (ii) an agent-centric threat model spanning
> perception, planning, memory, action, and coordination layers mapped to nine security goals; (iii) a
> comparative survey of CC-based defenses distinguishing findings that transfer from single-call
> inference versus what requires new agentic designs; and (iv) six open challenges including compound
> attestation for multi-hop agent chains and GPU-TEE performance at LLM scale. While several hardware
> trust primitives appear mature enough for targeted deployments, no broadly established end-to-end
> framework yet binds them into a coherent security substrate for production agentic AI.

### 4. [Notarized Agents: Receiver-Attested Confidential Receipts for AI Agent Actions](https://arxiv.org/abs/2606.04193)

- **arXiv:** [2606.04193](https://arxiv.org/abs/2606.04193)
- **Date:** published 2026-06-02
- **Authors:** Juan Figuera
- **Categories:** cs.CR, cs.AI, cs.DC
- **Citation:** Figuera, J. (2026). Notarized Agents: Receiver-Attested Confidential Receipts for AI Agent Actions. arXiv preprint. https://arxiv.org/abs/2606.04193v1

**Abstract:**

> Current AI agent observability is structurally compromised: the entity producing the activity log is
> the same entity whose activity is being logged. A compromised or buggy agent can omit, alter, or
> fabricate its own traces, and the operator running the agent has no independent way to detect
> tampering. We propose a class of protocols that resolves this by inverting the trust boundary: the
> service that receives an agent's call signs a receipt of what it observed using its own key,
> encrypts the receipt to the agent's owner, and publishes it to a public transparency log. The owner
> reconstructs a tamper-evident trail without trusting the agent or its operator. We instantiate the
> class as Sello, a protocol combining four properties absent in any current system: (P1) receiver-
> side signing, (P2) HPKE encryption to an owner public key bound to the authorization token via JWS,
> (P3) publication to a witness-cosigned Merkle log, and (P4) owner-side discovery by token reference.
> We describe the protocol, analyze its security under an adversary that controls the agent and its
> operator, present microbenchmarks of the cryptographic operations, and situate Sello among adjacent
> receipt-protocol work (Signet, AgentROA, Agent Passport System, draft-farley-acta, SCITT). We
> discuss known limitations including the suppression attack, service collusion, and the adoption-
> incentive problem.

### 5. [DAO-Agent: Zero Knowledge-Verified Incentives for Decentralized Multi-Agent Coordination](https://arxiv.org/abs/2512.20973)

- **arXiv:** [2512.20973](https://arxiv.org/abs/2512.20973)
- **Date:** published 2025-12-24
- **Authors:** Yihan Xia, Taotao Wang, Wenxin Xu, Shengli Zhang
- **Categories:** cs.MA
- **Citation:** Xia, Y., Wang, T., Xu, W., & Zhang, S. (2025). DAO-Agent: Zero Knowledge-Verified Incentives for Decentralized Multi-Agent Coordination. arXiv preprint. https://arxiv.org/abs/2512.20973v1

**Abstract:**

> Autonomous Large Language Model (LLM)-based multi-agent systems have emerged as a promising paradigm
> for facilitating cross-application and cross-organization collaborations. These autonomous agents
> often operate in trustless environments, where centralized coordination faces significant
> challenges, such as the inability to ensure transparent contribution measurement and equitable
> incentive distribution. While blockchain is frequently proposed as a decentralized coordination
> platform, it inherently introduces high on-chain computation costs and risks exposing sensitive
> execution information of the agents. Consequently, the core challenge lies in enabling auditable
> task execution and fair incentive distribution for autonomous LLM agents in trustless environments,
> while simultaneously preserving their strategic privacy and minimizing on-chain costs. To address
> this challenge, we propose DAO-Agent, a novel framework that integrates three key technical
> innovations: (1) an on-chain decentralized autonomous organization (DAO) governance mechanism for
> transparent coordination and immutable logging; (2) a ZKP mechanism approach that enables Shapley-
> based contribution measurement off-chain, and (3) a hybrid on-chain/off-chain architecture that
> verifies ZKP-validated contribution measurements on-chain with minimal computational overhead. We
> implement DAO-Agent and conduct end-to-end experiments using a crypto trading task as a case study.
> Experimental results demonstrate that DAO-Agent achieves up to 99.9% reduction in verification gas
> costs compared to naive on-chain alternatives, with constant-time verification complexity that
> remains stable as coalition size increases, thereby establishing a scalable foundation for agent
> coordination in decentralized environments.

### 6. [ZK-Value: A Practical Zero-Knowledge System for Verifiable Data Valuation](https://arxiv.org/abs/2605.03581)

- **arXiv:** [2605.03581](https://arxiv.org/abs/2605.03581)
- **Date:** published 2026-05-05
- **Authors:** Zhaoyu Wang, Pingchuan Ma, Zhantong Xue, Yuguang Zhou, Qixin Zhang, Xiaoqin Zhang, Shuai Wang
- **Categories:** cs.CR
- **Citation:** Wang, Z., Ma, P., Xue, Z., Zhou, Y., Zhang, Q., Zhang, X., & Wang, S. (2026). ZK-Value: A Practical Zero-Knowledge System for Verifiable Data Valuation. arXiv preprint. https://arxiv.org/abs/2605.03581v1

**Abstract:**

> Data valuation is a foundational task in data marketplaces, where a Shapley-value attribution
> determines how a buyer's payment is distributed among data providers. Typically, the marketplace
> operator runs this attribution alone, requiring participants and external auditors to trust scores
> they cannot independently recompute on the underlying private data. While zero-knowledge proofs
> (ZKPs) can theoretically reconcile this conflict between privacy and verifiability, existing ZK
> valuation systems fail to scale to real-world marketplace demands due to prohibitive proving times
> or the requirement to disclose validation cohorts. We present ZK-Value, a practical, end-to-end ZK
> data-valuation system. Our solution bridges the scalability gap through a fully co-designed
> architecture: (1) LSH-Shapley, a locality-based valuation primitive that replaces expensive pairwise
> distance metrics with per-bucket collision counts; (2) ZK-LSH-Shapley, a tailored ZKP protocol that
> drastically reduces witness size by encoding these counts into bucket-level histograms rather than
> naive per-pair tensors; and (3) structural proof-system optimizations, specifically super-oracle
> batching and sparsity skipping. Evaluated across 12 standard datasets, ZK-Value delivers valuation
> quality on par with state-of-the-art baselines (within 0.033 AUROC of exact KNN-Shapley), while
> generating proofs in seconds to minutes and outperforming specialized ZK baselines by 12.6x to 68.1x
> in proving time, with verification in under 4.6 s.

### 7. [Data Shapley: Equitable Valuation of Data for Machine Learning](https://arxiv.org/abs/1904.02868)

- **arXiv:** [1904.02868](https://arxiv.org/abs/1904.02868)
- **Date:** published 2019-04-05; updated 2019-06-10
- **Authors:** Amirata Ghorbani, James Zou
- **Categories:** stat.ML, cs.AI, cs.LG
- **Citation:** Ghorbani, A. & Zou, J. (2019). Data Shapley: Equitable Valuation of Data for Machine Learning. arXiv preprint. https://arxiv.org/abs/1904.02868v2

**Abstract:**

> As data becomes the fuel driving technological and economic growth, a fundamental challenge is how
> to quantify the value of data in algorithmic predictions and decisions. For example, in healthcare
> and consumer markets, it has been suggested that individuals should be compensated for the data that
> they generate, but it is not clear what is an equitable valuation for individual data. In this work,
> we develop a principled framework to address data valuation in the context of supervised machine
> learning. Given a learning algorithm trained on $n$ data points to produce a predictor, we propose
> data Shapley as a metric to quantify the value of each training datum to the predictor performance.
> Data Shapley value uniquely satisfies several natural properties of equitable data valuation. We
> develop Monte Carlo and gradient-based methods to efficiently estimate data Shapley values in
> practical settings where complex learning algorithms, including neural networks, are trained on
> large datasets. In addition to being equitable, extensive experiments across biomedical, image and
> synthetic data demonstrate that data Shapley has several other benefits: 1) it is more powerful than
> the popular leave-one-out or leverage score in providing insight on what data is more valuable for a
> given learning task; 2) low Shapley value data effectively capture outliers and corruptions; 3) high
> Shapley value data inform what type of new data to acquire to improve the predictor.

### 8. [Privacy-Preserving Decentralized AI with Confidential Computing](https://arxiv.org/abs/2410.13752)

- **arXiv:** [2410.13752](https://arxiv.org/abs/2410.13752)
- **Date:** published 2024-10-17; updated 2024-10-18
- **Authors:** Dayeol Lee, Jorge António, Hisham Khan
- **Categories:** cs.CR, cs.AI
- **Citation:** Lee, D., António, J., & Khan, H. (2024). Privacy-Preserving Decentralized AI with Confidential Computing. arXiv preprint. https://arxiv.org/abs/2410.13752v2

**Abstract:**

> This paper addresses privacy protection in decentralized Artificial Intelligence (AI) using
> Confidential Computing (CC) within the Atoma Network, a decentralized AI platform designed for the
> Web3 domain. Decentralized AI distributes AI services among multiple entities without centralized
> oversight, fostering transparency and robustness. However, this structure introduces significant
> privacy challenges, as sensitive assets such as proprietary models and personal data may be exposed
> to untrusted participants. Cryptography-based privacy protection techniques such as zero-knowledge
> machine learning (zkML) suffers prohibitive computational overhead. To address the limitation, we
> propose leveraging Confidential Computing (CC). Confidential Computing leverages hardware-based
> Trusted Execution Environments (TEEs) to provide isolation for processing sensitive data, ensuring
> that both model parameters and user data remain secure, even in decentralized, potentially untrusted
> environments. While TEEs face a few limitations, we believe they can bridge the privacy gap in
> decentralized AI. We explore how we can integrate TEEs into Atoma's decentralized framework.

### 9. [The Agent Economy: A Blockchain-Based Foundation for Autonomous AI Agents](https://arxiv.org/abs/2602.14219)

- **arXiv:** [2602.14219](https://arxiv.org/abs/2602.14219)
- **Date:** published 2026-02-15
- **Authors:** Minghui Xu
- **Categories:** cs.CR
- **Citation:** Xu, M. (2026). The Agent Economy: A Blockchain-Based Foundation for Autonomous AI Agents. arXiv preprint. https://arxiv.org/abs/2602.14219v1

**Abstract:**

> We propose the Agent Economy, a blockchain-based foundation where autonomous AI agents operate as
> economic peers to humans. Current agents lack independent legal identity, cannot hold assets, and
> cannot receive payments directly. We established fundamental differences between human and machine
> economic actors and demonstrated that existing human-centric infrastructure cannot support genuine
> agent autonomy. We showed that blockchain technology provides three critical properties enabling
> genuine agent autonomy: permissionless participation, trustless settlement, and machine-to-machine
> micropayments. We propose a five-layer architecture: (1) Physical Infrastructure (hardware & energy)
> through DePIN protocols; (2) Identity & Agency establishing on-chain sovereignty through W3C DIDs
> and reputation capital; (3) Cognitive & Tooling enabling intelligence via RAG and MCP; (4) Economic
> & Settlement ensuring financial autonomy through account abstraction; and (5) Collective Governance
> coordinating multi-agent systems through Agentic DAOs. We identify six core research challenges and
> examine ethical and regulatory implications. This paper lays groundwork for the Internet of Agents
> (IoA), a global decentralized network where autonomous machines and humans interact as equal
> economic participants.

### 10. [From Agent Traces to Trust: A Survey of Evidence Tracing and Execution Provenance in LLM Agents](https://arxiv.org/abs/2606.04990)

- **arXiv:** [2606.04990](https://arxiv.org/abs/2606.04990)
- **Date:** published 2026-06-03; updated 2026-06-16
- **Authors:** Yiqi Wang, Jiaqi Zhang, Taotao Cai, Zirui Liu, Qingqiang Sun, Zequn Sun, Zhangkai Wu, Manqing Dong, Mingkai Zhang, Xuefei Yin, Yanming Zhu
- **Categories:** cs.CR, cs.AI
- **Citation:** Wang, Y., Zhang, J., Cai, T., Liu, Z., Sun, Q., Sun, Z., Wu, Z., Dong, M., Zhang, M., Yin, X., & Zhu, Y. (2026). From Agent Traces to Trust: A Survey of Evidence Tracing and Execution Provenance in LLM Agents. arXiv preprint. https://arxiv.org/abs/2606.04990v3

**Abstract:**

> Large language model (LLM)-based agents are evolving from passive text generators into autonomous
> systems capable of planning, tool use, retrieval, memory access, environmental interaction, and
> multi-agent collaboration. These capabilities expand agent autonomy, but also make agent behavior
> harder to verify, debug, and audit. Final-answer accuracy alone cannot explain how an output was
> produced, which evidence supported each claim, whether tool calls were justified, how memory
> influenced later decisions, or where failures originated. This survey examines evidence tracing and
> execution provenance as foundations for process-level accountability in trustworthy LLM agents. We
> define execution provenance as the typed graph of an agent execution and evidence tracing as its
> projection onto evidence-support relations. This perspective connects retrieval grounding, claim
> support, tool-use safety, memory lineage, observability, debugging, audit, and recovery within a
> unified framework. We introduce a taxonomy covering trace sources, evidence and execution units,
> provenance relations, tracing granularity and timing, representation forms, and trust functions. We
> then review key methodological directions, including provenance representation, evidence
> attribution, tool-use provenance, runtime guardrails, provenance-bearing memory, observability, and
> failure diagnosis. Finally, we discuss benchmarks, datasets, metrics, and open challenges for
> building provenance-aware, auditable, and recoverable agent systems.

## Confidential computing and private inference substrate

### 11. [AgenTEE: Confidential LLM Agent Execution on Edge Devices](https://arxiv.org/abs/2604.18231)

- **arXiv:** [2604.18231](https://arxiv.org/abs/2604.18231)
- **Date:** published 2026-04-20; updated 2026-05-06
- **Authors:** Sina Abdollahi, Mohammad M Maheri, Javad Forough, Amir Al Sadi, Josh Millar, David Kotz, Marios Kogias, Hamed Haddadi
- **Categories:** cs.CR, cs.OS
- **DOI:** 10.1145/3805621.3807660
- **Citation:** Abdollahi, S., Maheri, M. M., Forough, J., Sadi, A. A., Millar, J., Kotz, D., Kogias, M., & Haddadi, H. (2026). AgenTEE: Confidential LLM Agent Execution on Edge Devices. arXiv preprint. https://arxiv.org/abs/2604.18231v2

**Abstract:**

> Large Language Model (LLM) agents provide powerful automation capabilities, but they also create a
> substantially broader attack surface than traditional applications due to their tight integration
> with non-deterministic models and third-party services. While current deployments primarily rely on
> cloud-hosted services, emerging designs increasingly execute agents directly on edge devices to
> reduce latency and enhance user privacy. However, securely hosting such complex agent pipelines on
> edge devices remains challenging. These deployments must protect proprietary assets (e.g., system
> prompts and model weights) and sensitive runtime state on heterogeneous platforms that are
> vulnerable to software attacks and potentially controlled by malicious users. To address these
> challenges, we present AgenTEE, a system for deploying confidential agent pipelines on edge devices.
> AgenTEE places the agent runtime, inference engine, and third-party applications into independently
> attested confidential virtual machines (cVMs) and mediates their interaction through explicit,
> verifiable communication channels. Built on Arm Confidential Compute Architecture (CCA), a recent
> extension to Arm platforms, AgenTEE enforces strong system-level isolation of sensitive assets and
> runtime state. Our evaluation shows that such multi-cVMs system is practical, achieving near-native
> performance with less than 5.15% runtime overhead compared to commodity OS multi-process
> deployments.

### 12. [OpenPCC: Open and Confidential LLM Serving on Commodity TEEs](https://arxiv.org/abs/2606.11145)

- **arXiv:** [2606.11145](https://arxiv.org/abs/2606.11145)
- **Date:** published 2026-06-09
- **Authors:** Haoling Zhou, Shixuan Zhao, Chao Wang, Zhiqiang Lin
- **Categories:** cs.CR
- **Citation:** Zhou, H., Zhao, S., Wang, C., & Lin, Z. (2026). OpenPCC: Open and Confidential LLM Serving on Commodity TEEs. arXiv preprint. https://arxiv.org/abs/2606.11145v1

**Abstract:**

> Generative AI applications such as personal AI agents, image generators, and chat assistants offer
> advanced capabilities to improve user experience. Behind the scenes, Large Language Models (LLMs)
> that power these services require a massive amount of computation and are usually deployed in the
> cloud, available as APIs, meaning that a user's request has to be sent to a Cloud Inference Service
> (CIS) for processing. However, the strong capabilities of LLM also mean that user's requests now
> contain much more personal sensitive or enterprise confidential information, demanding equally
> strong protection in CIS. While early industry efforts such as Apple Private Cloud Compute (PCC) and
> Google Private AI Compute have emerged to show the potential of secure CIS, they are not adoptable
> for deployment by others due to their reliance on proprietary hardware and closed ecosystem. In
> addition, they all suffer from their own design glitches that can undermine the ambitious goal of
> bringing in true privacy protection to end users. In this paper, we present our analysis of the
> fundamental requirements of building a secure yet open CIS. We then present OpenPCC, a Confidential
> CIS framework that does not rely on proprietary hardware but instead uses commercially available
> TEEs. We implement an open-source prototype and characterize it end-to-end on a Llama-3 8B vLLM
> workload, separating OpenPCC's own cost from the underlying TEE hardware. Our analysis and
> evaluation demonstrated the feasibility and security of the system.

### 13. [Your Inference Request Will Become a Black Box: Confidential Inference for Cloud-based Large Language Models](https://arxiv.org/abs/2603.00196)

- **arXiv:** [2603.00196](https://arxiv.org/abs/2603.00196)
- **Date:** published 2026-02-27
- **Authors:** Chung-ju Huang, Huiqiang Zhao, Yuanpeng He, Lijian Li, Wenpin Jiao, Zhi Jin, Peixuan Chen, Leye Wang
- **Categories:** cs.CR, cs.AI, cs.CL
- **Citation:** Huang, C., Zhao, H., He, Y., Li, L., Jiao, W., Jin, Z., Chen, P., & Wang, L. (2026). Your Inference Request Will Become a Black Box: Confidential Inference for Cloud-based Large Language Models. arXiv preprint. https://arxiv.org/abs/2603.00196v1

**Abstract:**

> The increasing reliance on cloud-hosted Large Language Models (LLMs) exposes sensitive client data,
> such as prompts and responses, to potential privacy breaches by service providers. Existing
> approaches fail to ensure privacy, maintain model performance, and preserve computational efficiency
> simultaneously. To address this challenge, we propose Talaria, a confidential inference framework
> that partitions the LLM pipeline to protect client data without compromising the cloud's model
> intellectual property or inference quality. Talaria executes sensitive, weight-independent
> operations within a client-controlled Confidential Virtual Machine (CVM) while offloading weight-
> dependent computations to the cloud GPUs. The interaction between these environments is secured by
> our Reversible Masked Outsourcing (ReMO) protocol, which uses a hybrid masking technique to
> reversibly obscure intermediate data before outsourcing computations. Extensive evaluations show
> that Talaria can defend against state-of-the-art token inference attacks, reducing token
> reconstruction accuracy from over 97.5% to an average of 1.34%, all while being a lossless mechanism
> that guarantees output identical to the original model without significantly decreasing efficiency
> and scalability. To the best of our knowledge, this is the first work that ensures clients' prompts
> and responses remain inaccessible to the cloud, while also preserving model privacy, performance,
> and efficiency.

### 14. [Confidential LLM Inference: Performance and Cost Across CPU and GPU TEEs](https://arxiv.org/abs/2509.18886)

- **arXiv:** [2509.18886](https://arxiv.org/abs/2509.18886)
- **Date:** published 2025-09-23
- **Authors:** Marcin Chrapek, Marcin Copik, Etienne Mettaz, Torsten Hoefler
- **Categories:** cs.PF, cs.AR, cs.CR, cs.LG
- **Citation:** Chrapek, M., Copik, M., Mettaz, E., & Hoefler, T. (2025). Confidential LLM Inference: Performance and Cost Across CPU and GPU TEEs. arXiv preprint. https://arxiv.org/abs/2509.18886v1

**Abstract:**

> Large Language Models (LLMs) are increasingly deployed on converged Cloud and High-Performance
> Computing (HPC) infrastructure. However, as LLMs handle confidential inputs and are fine-tuned on
> costly, proprietary datasets, their heightened security requirements slow adoption in privacy-
> sensitive sectors such as healthcare and finance. We investigate methods to address this gap and
> propose Trusted Execution Environments (TEEs) as a solution for securing end-to-end LLM inference.
> We validate their practicality by evaluating these compute-intensive workloads entirely within CPU
> and GPU TEEs. On the CPU side, we conduct an in-depth study running full Llama2 inference pipelines
> (7B, 13B, 70B) inside Intel's TDX and SGX, accelerated by Advanced Matrix Extensions (AMX). We
> derive 12 insights, including that across various data types, batch sizes, and input lengths, CPU
> TEEs impose under 10% throughput and 20% latency overheads, further reduced by AMX. We run LLM
> inference on NVIDIA H100 Confidential Compute GPUs, contextualizing our CPU findings and observing
> throughput penalties of 4-8% that diminish as batch and input sizes grow. By comparing performance,
> cost, and security trade-offs, we show how CPU TEEs can be more cost-effective or secure than their
> GPU counterparts. To our knowledge, our work is the first to comprehensively demonstrate the
> performance and practicality of modern TEEs across both CPUs and GPUs for enabling confidential LLMs
> (cLLMs).

### 15. [Towards Confidential and Efficient LLM Inference with Dual Privacy Protection](https://arxiv.org/abs/2509.09091)

- **arXiv:** [2509.09091](https://arxiv.org/abs/2509.09091)
- **Date:** published 2025-09-11
- **Authors:** Honglan Yu, Yibin Wang, Feifei Dai, Dong Liu, Haihui Fan, Xiaoyan Gu
- **Categories:** cs.CR, cs.AI
- **Citation:** Yu, H., Wang, Y., Dai, F., Liu, D., Fan, H., & Gu, X. (2025). Towards Confidential and Efficient LLM Inference with Dual Privacy Protection. arXiv preprint. https://arxiv.org/abs/2509.09091v1

**Abstract:**

> CPU-based trusted execution environments (TEEs) and differential privacy (DP) have gained wide
> applications for private inference. Due to high inference latency in TEEs, researchers use
> partition-based approaches that offload linear model components to GPUs. However, dense nonlinear
> layers of large language models (LLMs) result in significant communication overhead between TEEs and
> GPUs. DP-based approaches apply random noise to protect data privacy, but this compromises LLM
> performance and semantic understanding. To overcome the above drawbacks, this paper proposes CMIF, a
> Confidential and efficient Model Inference Framework. CMIF confidentially deploys the embedding
> layer in the client-side TEE and subsequent layers on GPU servers. Meanwhile, it optimizes the
> Report-Noisy-Max mechanism to protect sensitive inputs with a slight decrease in model performance.
> Extensive experiments on Llama-series models demonstrate that CMIF reduces additional inference
> overhead in TEEs while preserving user data privacy.

### 16. [Confidential Prompting: Privacy-preserving LLM Inference on Cloud](https://arxiv.org/abs/2409.19134)

- **arXiv:** [2409.19134](https://arxiv.org/abs/2409.19134)
- **Date:** published 2024-09-27; updated 2025-11-19
- **Authors:** Caihua Li, In Gim, Lin Zhong
- **Categories:** cs.CR, cs.CL
- **Citation:** Li, C., Gim, I., & Zhong, L. (2024). Confidential Prompting: Privacy-preserving LLM Inference on Cloud. arXiv preprint. https://arxiv.org/abs/2409.19134v5

**Abstract:**

> This paper introduces a vision of confidential prompting: securing user prompts from an untrusted,
> cloud-hosted large language model (LLM) while preserving model confidentiality, output invariance,
> and compute efficiency. As a first step toward this vision, we present Petridish, a system built on
> top of confidential computing and its core contribution, a novel technology called Secure
> Partitioned Decoding (SPD). Petridish runs the LLM service inside a confidential virtual machine
> (CVM), which protects the secrets, i.e., the LLM parameters and user prompts, from adversaries
> outside the CVM. Importantly, it splits the LLM service for a user into two processes, using SPD: a
> per-user process performs prefill with the user prompts and computes attention scores during
> decoding; a service process, shared by all users, batches the attention scores from per-user
> processes and generates output tokens for all users. Both the LLM provider and the users trust
> Petridish's CVM and its operating system, which guarantees isolation between processes and limits
> their outbound network capabilities to control information flow. The CVM's attestation capability
> and its open-source software stack enable Petridish to provide auditable protection of both user
> prompt and LLM confidentiality. Together, Petridish maintains full utility of LLM service and
> enables practical, privacy-preserving cloud-hosted LLM inference for sensitive applications, such as
> processing personal data, clinical records, and financial documents.

### 17. [Bifrost: Hybrid TEE-FHE Inference for Privacy-Preserving Transformer and LLM Serving](https://arxiv.org/abs/2606.17421)

- **arXiv:** [2606.17421](https://arxiv.org/abs/2606.17421)
- **Date:** published 2026-06-16
- **Authors:** Chenghao Chen, Kailun Qin, Xiaolin Zhang, Chi Zhang, Dawu Gu
- **Categories:** cs.CR
- **Citation:** Chen, C., Qin, K., Zhang, X., Zhang, C., & Gu, D. (2026). Bifrost: Hybrid TEE-FHE Inference for Privacy-Preserving Transformer and LLM Serving. arXiv preprint. https://arxiv.org/abs/2606.17421v1

**Abstract:**

> Cloud-hosted transformer and large language model (LLM) inference creates a direct confidentiality
> problem: user prompts may contain sensitive code, business data, personal information, or regulated
> documents, yet remote serving exposes intermediate state to the cloud software stack and accelerator
> runtime. Fully homomorphic encryption (FHE) keeps accelerator-side execution ciphertext-only, but
> end-to-end LLM inference remains expensive because linear layers are interleaved with non-linear,
> cache-state, and refresh-sensitive operators. CPU trusted execution environments (TEEs) can execute
> those operators natively, but a CPU TEE alone does not define how an untrusted accelerator should
> participate. We present Bifrost, a hybrid TEE-FHE serving architecture in which secrets are
> provisioned only to an attested CPU TEE, while the accelerator, device memory, driver/runtime stack,
> and host software remain outside the trusted computing base. Bifrost uses FHE as a secure delegation
> mechanism for projection and feed-forward linear layers on accelerator-backed CKKS, while non-linear
> operators, attention-side control logic, KV-state transitions, and decrypt-then-encrypt refresh
> execute inside the CPU TEE. Bifrost+ further applies a prefill/decode split: prompt-side KV state is
> built inside the CPU TEE, and only decode-side state enters the hybrid ciphertext path. In an
> estimator-style comparison matching Euston's methodology, Bifrost reduces projected latency by 9.25x
> on GPT-2 (1.5B) and 9.91x on LLaMA 3 (8B). In direct CKKS/FHE deployments, Bifrost+ reduces TTFT by
> 14.6-45.8x on GPT-2 (124M) and 15.3-53.4x on Qwen3 (0.6B). The systems lesson is selective encrypted
> execution: use FHE only where ciphertext-only accelerator delegation is required, and keep non-
> linear, refresh, and prompt-side work inside the CPU TEE.

### 18. [TZ-LLM: Protecting On-Device Large Language Models with Arm TrustZone](https://arxiv.org/abs/2511.13717)

- **arXiv:** [2511.13717](https://arxiv.org/abs/2511.13717)
- **Date:** published 2025-11-17
- **Authors:** Xunjie Wang, Jiacheng Shi, Zihan Zhao, Yang Yu, Zhichao Hua, Jinyu Gu
- **Categories:** cs.CR
- **Citation:** Wang, X., Shi, J., Zhao, Z., Yu, Y., Hua, Z., & Gu, J. (2025). TZ-LLM: Protecting On-Device Large Language Models with Arm TrustZone. arXiv preprint. https://arxiv.org/abs/2511.13717v1

**Abstract:**

> Large Language Models (LLMs) deployed on mobile devices offer benefits like user privacy and reduced
> network latency, but introduce a significant security risk: the leakage of proprietary models to end
> users. To mitigate this risk, we propose a system design for protecting on-device LLMs using Arm
> Trusted Execution Environment (TEE), TrustZone. Our system addresses two primary challenges: (1) The
> dilemma between memory efficiency and fast inference (caching model parameters within TEE memory).
> (2) The lack of efficient and secure Neural Processing Unit (NPU) time-sharing between Rich
> Execution Environment (REE) and TEE. Our approach incorporates two key innovations. First, we employ
> pipelined restoration, leveraging the deterministic memory access patterns of LLM inference to
> prefetch parameters on demand, hiding memory allocation, I/O and decryption latency under
> computation time. Second, we introduce a co-driver design, creating a minimal data plane NPU driver
> in the TEE that collaborates with the full-fledged REE driver. This reduces the TEE TCB size and
> eliminates control plane reinitialization overhead during NPU world switches. We implemented our
> system on the emerging OpenHarmony OS and the llama.cpp inference framework, and evaluated it with
> various LLMs on an Arm Rockchip device. Compared to a strawman TEE baseline lacking our
> optimizations, our system reduces TTFT by up to 90.9% and increases decoding speed by up to 23.2%.

### 19. [AttestLLM: Efficient Attestation Framework for Billion-scale On-device LLMs](https://arxiv.org/abs/2509.06326)

- **arXiv:** [2509.06326](https://arxiv.org/abs/2509.06326)
- **Date:** published 2025-09-08; updated 2026-02-23
- **Authors:** Ruisi Zhang, Yifei Zhao, Neusha Javidnia, Mengxin Zheng, Farinaz Koushanfar
- **Categories:** cs.CR, cs.AI
- **Citation:** Zhang, R., Zhao, Y., Javidnia, N., Zheng, M., & Koushanfar, F. (2025). AttestLLM: Efficient Attestation Framework for Billion-scale On-device LLMs. arXiv preprint. https://arxiv.org/abs/2509.06326v2

**Abstract:**

> As on-device LLMs(e.g., Apple on-device Intelligence) are widely adopted to reduce network
> dependency, improve privacy, and enhance responsiveness, verifying the legitimacy of models running
> on local devices becomes critical. Existing attestation techniques are not suitable for billion-
> parameter Large Language Models (LLMs), struggling to remain both time- and memory-efficient while
> addressing emerging threats in the LLM era. In this paper, we present AttestLLM, the first-of-its-
> kind attestation framework to protect the hardware-level intellectual property (IP) of device
> vendors by ensuring that only authorized LLMs can execute on target platforms. AttestLLM leverages
> an algorithm/software/hardware co-design approach to embed robust watermarking signatures onto the
> activation distributions of LLM building blocks. It also optimizes the attestation protocol within
> the Trusted Execution Environment (TEE), providing efficient verification without compromising
> inference throughput. Extensive proof-of-concept evaluations on LLMs from Llama, Qwen, and Phi
> families for on-device use cases demonstrate AttestLLM's attestation reliability, fidelity, and
> efficiency. Furthermore, AttestLLM enforces model legitimacy and exhibits resilience against model
> replacement and forgery attacks.

### 20. [Privacy-Preserving Inference in Machine Learning Services Using Trusted Execution Environments](https://arxiv.org/abs/1912.03485)

- **arXiv:** [1912.03485](https://arxiv.org/abs/1912.03485)
- **Date:** published 2019-12-07
- **Authors:** Krishna Giri Narra, Zhifeng Lin, Yongqin Wang, Keshav Balasubramaniam, Murali Annavaram
- **Categories:** cs.LG, cs.CR, cs.CV, stat.ML
- **Citation:** Narra, K. G., Lin, Z., Wang, Y., Balasubramaniam, K., & Annavaram, M. (2019). Privacy-Preserving Inference in Machine Learning Services Using Trusted Execution Environments. arXiv preprint. https://arxiv.org/abs/1912.03485v1

**Abstract:**

> This work presents Origami, which provides privacy-preserving inference for large deep neural
> network (DNN) models through a combination of enclave execution, cryptographic blinding,
> interspersed with accelerator-based computation. Origami partitions the ML model into multiple
> partitions. The first partition receives the encrypted user input within an SGX enclave. The enclave
> decrypts the input and then applies cryptographic blinding to the input data and the model
> parameters. Cryptographic blinding is a technique that adds noise to obfuscate data. Origami sends
> the obfuscated data for computation to an untrusted GPU/CPU. The blinding and de-blinding factors
> are kept private by the SGX enclave, thereby preventing any adversary from denoising the data, when
> the computation is offloaded to a GPU/CPU. The computed output is returned to the enclave, which
> decodes the computation on noisy data using the unblinding factors privately stored within SGX. This
> process may be repeated for each DNN layer, as has been done in prior work Slalom. However, the
> overhead of blinding and unblinding the data is a limiting factor to scalability. Origami relies on
> the empirical observation that the feature maps after the first several layers can not be used, even
> by a powerful conditional GAN adversary to reconstruct input. Hence, Origami dynamically switches to
> executing the rest of the DNN layers directly on an accelerator without needing any further
> cryptographic blinding intervention to preserve privacy. We empirically demonstrate that using
> Origami, a conditional GAN adversary, even with an unlimited inference budget, cannot reconstruct
> the input. We implement and demonstrate the performance gains of Origami using the VGG-16 and VGG-19
> models. Compared to running the entire VGG-19 model within SGX, Origami inference improves the
> performance of private inference from 11x while using Slalom to 15.1x.

### 21. [Memory-Efficient Deep Learning Inference in Trusted Execution Environments](https://arxiv.org/abs/2104.15109)

- **arXiv:** [2104.15109](https://arxiv.org/abs/2104.15109)
- **Date:** published 2021-04-30; updated 2021-09-30
- **Authors:** Jean-Baptiste Truong, William Gallagher, Tian Guo, Robert J. Walls
- **Categories:** cs.CR, cs.LG, cs.PF
- **Citation:** Truong, J., Gallagher, W., Guo, T., & Walls, R. J. (2021). Memory-Efficient Deep Learning Inference in Trusted Execution Environments. arXiv preprint. https://arxiv.org/abs/2104.15109v2

**Abstract:**

> This study identifies and proposes techniques to alleviate two key bottlenecks to executing deep
> neural networks in trusted execution environments (TEEs): page thrashing during the execution of
> convolutional layers and the decryption of large weight matrices in fully-connected layers. For the
> former, we propose a novel partitioning scheme, y-plane partitioning, designed to (i) provide
> consistent execution time when the layer output is large compared to the TEE secure memory; and (ii)
> significantly reduce the memory footprint of convolutional layers. For the latter, we leverage
> quantization and compression. In our evaluation, the proposed optimizations incurred latency
> overheads ranging from 1.09X to 2X baseline for a wide range of TEE sizes; in contrast, an
> unmodified implementation incurred latencies of up to 26X when running inside of the TEE.

### 22. [Privado: Practical and Secure DNN Inference with Enclaves](https://arxiv.org/abs/1810.00602)

- **arXiv:** [1810.00602](https://arxiv.org/abs/1810.00602)
- **Date:** published 2018-10-01; updated 2019-09-05
- **Authors:** Karan Grover, Shruti Tople, Shweta Shinde, Ranjita Bhagwan, Ramachandran Ramjee
- **Categories:** cs.CR, cs.AI, cs.CV
- **Citation:** Grover, K., Tople, S., Shinde, S., Bhagwan, R., & Ramjee, R. (2018). Privado: Practical and Secure DNN Inference with Enclaves. arXiv preprint. https://arxiv.org/abs/1810.00602v2

**Abstract:**

> Cloud providers are extending support for trusted hardware primitives such as Intel SGX.
> Simultaneously, the field of deep learning is seeing enormous innovation as well as an increase in
> adoption. In this paper, we ask a timely question: "Can third-party cloud services use Intel SGX
> enclaves to provide practical, yet secure DNN Inference-as-a-service?" We first demonstrate that DNN
> models executing inside enclaves are vulnerable to access pattern based attacks. We show that by
> simply observing access patterns, an attacker can classify encrypted inputs with 97% and 71% attack
> accuracy for MNIST and CIFAR10 datasets on models trained to achieve 99% and 79% original accuracy
> respectively. This motivates the need for PRIVADO, a system we have designed for secure, easy-to-
> use, and performance efficient inference-as-a-service. PRIVADO is input-oblivious: it transforms any
> deep learning framework that is written in C/C++ to be free of input-dependent access patterns thus
> eliminating the leakage. PRIVADO is fully-automated and has a low TCB: with zero developer effort,
> given an ONNX description of a model, it generates compact and enclave-compatible code which can be
> deployed on an SGX cloud platform. PRIVADO incurs low performance overhead: we use PRIVADO with
> Torch framework and show its overhead to be 17.18% on average on 11 different contemporary neural
> networks.

### 23. [Slalom: Fast, Verifiable and Private Execution of Neural Networks in Trusted Hardware](https://arxiv.org/abs/1806.03287)

- **arXiv:** [1806.03287](https://arxiv.org/abs/1806.03287)
- **Date:** published 2018-06-08; updated 2019-02-27
- **Authors:** Florian Tramèr, Dan Boneh
- **Categories:** stat.ML, cs.CR, cs.LG
- **Citation:** Tramèr, F. & Boneh, D. (2018). Slalom: Fast, Verifiable and Private Execution of Neural Networks in Trusted Hardware. arXiv preprint. https://arxiv.org/abs/1806.03287v2

**Abstract:**

> As Machine Learning (ML) gets applied to security-critical or sensitive domains, there is a growing
> need for integrity and privacy for outsourced ML computations. A pragmatic solution comes from
> Trusted Execution Environments (TEEs), which use hardware and software protections to isolate
> sensitive computations from the untrusted software stack. However, these isolation guarantees come
> at a price in performance, compared to untrusted alternatives. This paper initiates the study of
> high performance execution of Deep Neural Networks (DNNs) in TEEs by efficiently partitioning DNN
> computations between trusted and untrusted devices. Building upon an efficient outsourcing scheme
> for matrix multiplication, we propose Slalom, a framework that securely delegates execution of all
> linear layers in a DNN from a TEE (e.g., Intel SGX or Sanctum) to a faster, yet untrusted, co-
> located processor. We evaluate Slalom by running DNNs in an Intel SGX enclave, which selectively
> delegates work to an untrusted GPU. For canonical DNNs (VGG16, MobileNet and ResNet variants) we
> obtain 6x to 20x increases in throughput for verifiable inference, and 4x to 11x for verifiable and
> private inference.

### 24. [Confidential Computing across Edge-to-Cloud for Machine Learning: A Survey Study](https://arxiv.org/abs/2307.16447)

- **arXiv:** [2307.16447](https://arxiv.org/abs/2307.16447)
- **Date:** published 2023-07-31
- **Authors:** SM Zobaed, Mohsen Amini Salehi
- **Categories:** cs.DC, cs.CR
- **Citation:** Zobaed, S. & Salehi, M. A. (2023). Confidential Computing across Edge-to-Cloud for Machine Learning: A Survey Study. arXiv preprint. https://arxiv.org/abs/2307.16447v1

**Abstract:**

> Confidential computing has gained prominence due to the escalating volume of data-driven
> applications (e.g., machine learning and big data) and the acute desire for secure processing of
> sensitive data, particularly, across distributed environments, such as edge-to-cloud continuum.
> Provided that the works accomplished in this emerging area are scattered across various research
> fields, this paper aims at surveying the fundamental concepts, and cutting-edge software and
> hardware solutions developed for confidential computing using trusted execution environments,
> homomorphic encryption, and secure enclaves. We underscore the significance of building trust in
> both hardware and software levels and delve into their applications particularly for machine
> learning (ML) applications. While substantial progress has been made, there are some barely-explored
> areas that need extra attention from the researchers and practitioners in the community to improve
> confidentiality aspects, develop more robust attestation mechanisms, and to address vulnerabilities
> of the existing trusted execution environments. Providing a comprehensive taxonomy of the
> confidential computing landscape, this survey enables researchers to advance this field to
> ultimately ensure the secure processing of users' sensitive data across a multitude of applications
> and computing tiers.

### 25. [A Survey of Secure Computation Using Trusted Execution Environments](https://arxiv.org/abs/2302.12150)

- **arXiv:** [2302.12150](https://arxiv.org/abs/2302.12150)
- **Date:** published 2023-02-23
- **Authors:** Xiaoguo Li, Bowen Zhao, Guomin Yang, Tao Xiang, Jian Weng, Robert H. Deng
- **Categories:** cs.CR, cs.AI, cs.DB
- **Citation:** Li, X., Zhao, B., Yang, G., Xiang, T., Weng, J., & Deng, R. H. (2023). A Survey of Secure Computation Using Trusted Execution Environments. arXiv preprint. https://arxiv.org/abs/2302.12150v1

**Abstract:**

> As an essential technology underpinning trusted computing, the trusted execution environment (TEE)
> allows one to launch computation tasks on both on- and off-premises data while assuring
> confidentiality and integrity. This article provides a systematic review and comparison of TEE-based
> secure computation protocols. We first propose a taxonomy that classifies secure computation
> protocols into three major categories, namely secure outsourced computation, secure distributed
> computation and secure multi-party computation. To enable a fair comparison of these protocols, we
> also present comprehensive assessment criteria with respect to four aspects: setting, methodology,
> security and performance. Based on these criteria, we review, discuss and compare the state-of-the-
> art TEE-based secure computation protocols for both general-purpose computation functions and
> special-purpose ones, such as privacy-preserving machine learning and encrypted database queries. To
> the best of our knowledge, this article is the first survey to review TEE-based secure computation
> protocols and the comprehensive comparison can serve as a guideline for selecting suitable protocols
> for deployment in practice. Finally, we also discuss several future research directions and
> challenges.

### 26. [Confidential Attestation: Efficient in-Enclave Verification of Privacy Policy Compliance](https://arxiv.org/abs/2007.10513)

- **arXiv:** [2007.10513](https://arxiv.org/abs/2007.10513)
- **Date:** published 2020-07-20
- **Authors:** Weijie Liu, Wenhao Wang, Xiaofeng Wang, Xiaozhu Meng, Yaosong Lu, Hongbo Chen, Xinyu Wang, Qingtao Shen, Kai Chen, Haixu Tang, Yi Chen, Luyi Xing
- **Categories:** cs.CR
- **Citation:** Liu, W., Wang, W., Wang, X., Meng, X., Lu, Y., Chen, H., Wang, X., Shen, Q., Chen, K., Tang, H., Chen, Y., & Xing, L. (2020). Confidential Attestation: Efficient in-Enclave Verification of Privacy Policy Compliance. arXiv preprint. https://arxiv.org/abs/2007.10513v1

**Abstract:**

> A trusted execution environment (TEE) such as Intel Software Guard Extension (SGX) runs a remote
> attestation to prove to a data owner the integrity of the initial state of an enclave, including the
> program to operate on her data. For this purpose, the data-processing program is supposed to be open
> to the owner, so its functionality can be evaluated before trust can be established. However,
> increasingly there are application scenarios in which the program itself needs to be protected. So
> its compliance with privacy policies as expected by the data owner should be verified without
> exposing its code. To this end, this paper presents CAT, a new model for TEE-based confidential
> attestation. Our model is inspired by Proof-Carrying Code, where a code generator produces proof
> together with the code and a code consumer verifies the proof against the code on its compliance
> with security policies. Given that the conventional solutions do not work well under the resource-
> limited and TCB-frugal TEE, we propose a new design that allows an untrusted out-enclave generator
> to analyze the source code of a program when compiling it into binary and a trusted in-enclave
> consumer efficiently verifies the correctness of the instrumentation and the presence of other
> protection before running the binary. Our design strategically moves most of the workload to the
> code generator, which is responsible for producing well-formatted and easy-to-check code, while
> keeping the consumer simple. Also, the whole consumer can be made public and verified through a
> conventional attestation. We implemented this model on Intel SGX and demonstrate that it introduces
> a very small part of TCB. We also thoroughly evaluated its performance on micro- and macro-
> benchmarks and real-world applications, showing that the new design only incurs a small overhead
> when enforcing several categories of security policies.

### 27. [Attestation Mechanisms for Trusted Execution Environments Demystified](https://arxiv.org/abs/2206.03780)

- **arXiv:** [2206.03780](https://arxiv.org/abs/2206.03780)
- **Date:** published 2022-06-08; updated 2022-09-23
- **Authors:** Jämes Ménétrey, Christian Göttel, Anum Khurshid, Marcelo Pasin, Pascal Felber, Valerio Schiavoni, Shahid Raza
- **Categories:** cs.CR, cs.DC
- **DOI:** 10.1007/978-3-031-16092-9_7
- **Citation:** Ménétrey, J., Göttel, C., Khurshid, A., Pasin, M., Felber, P., Schiavoni, V., & Raza, S. (2022). Attestation Mechanisms for Trusted Execution Environments Demystified. arXiv preprint. https://arxiv.org/abs/2206.03780v2

**Abstract:**

> Attestation is a fundamental building block to establish trust over software systems. When used in
> conjunction with trusted execution environments, it guarantees the genuineness of the code executed
> against powerful attackers and threats, paving the way for adoption in several sensitive application
> domains. This paper reviews remote attestation principles and explains how the modern and
> industrially well-established trusted execution environments Intel SGX, Arm TrustZone and AMD SEV,
> as well as emerging RISC-V solutions, leverage these mechanisms.

### 28. [Aegon: Auditable AI Content Access with Ledger-Bound Tokens and Hardware-Attested Mobile Receipts](https://arxiv.org/abs/2604.06693)

- **arXiv:** [2604.06693](https://arxiv.org/abs/2604.06693)
- **Date:** published 2026-04-08
- **Authors:** Amrish Baskaran, Nirbhay Pherwani, Raghul Krishnan
- **Categories:** cs.CR, cs.CY
- **Citation:** Baskaran, A., Pherwani, N., & Krishnan, R. (2026). Aegon: Auditable AI Content Access with Ledger-Bound Tokens and Hardware-Attested Mobile Receipts. arXiv preprint. https://arxiv.org/abs/2604.06693v1

**Abstract:**

> Recent standards such as RSL address AI content policy declaration -- telling AI systems what the
> licensing terms are. However, no existing system provides audit infrastructure -- tamper-evident
> licensing transaction records with independently verifiable proofs that those records have not been
> retroactively modified. We describe Aegon, a protocol that extends standard JWT tokens with content-
> specific licensing claims and maintains a Certificate Transparency-style Merkle tree over an append-
> only transaction ledger, enabling third-party auditors to independently verify that specific content
> licensing transactions were recorded and have not been retroactively modified. Publishers validate
> tokens at the edge using standard JWKS with no broker dependency in the content delivery path. A
> signed provenance event log tracks content through AI transformation stages (chunking, embedding,
> retrieval, citation), bound to ledger entries by transaction ID. We further describe hardware-
> attested compliance receipts for on-device Android AI agents using StrongBox secure element
> attestation -- to our knowledge, the first application of hardware-attested compliance receipts to
> AI content licensing. Existing DRM systems use hardware-backed keys for content decryption but do
> not produce verifiable compliance receipts for audit trails. We describe a reference architecture
> and an evaluation methodology for measuring protocol overhead. The protocol runs entirely over
> standard HTTPS and is designed to complement existing licensing standards rather than replace them.

### 29. [A Confidential Computing Transparency Framework for a Comprehensive Trust Chain](https://arxiv.org/abs/2409.03720)

- **arXiv:** [2409.03720](https://arxiv.org/abs/2409.03720)
- **Date:** published 2024-09-05; updated 2024-12-05
- **Authors:** Ceren Kocaoğullar, Tina Marjanov, Ivan Petrov, Ben Laurie, Al Cutter, Christoph Kern, Alice Hutchings, Alastair R. Beresford
- **Categories:** cs.CR
- **Citation:** Kocaoğullar, C., Marjanov, T., Petrov, I., Laurie, B., Cutter, A., Kern, C., Hutchings, A., & Beresford, A. R. (2024). A Confidential Computing Transparency Framework for a Comprehensive Trust Chain. arXiv preprint. https://arxiv.org/abs/2409.03720v2

**Abstract:**

> Confidential Computing enhances privacy of data in-use through hardware-based Trusted Execution
> Environments (TEEs) that use attestation to verify their integrity, authenticity, and certain
> runtime properties, along with those of the binaries they execute. However, TEEs require user trust,
> as attestation alone cannot guarantee the absence of vulnerabilities or backdoors. Enhanced
> transparency can mitigate the reliance on naive trust. Some organisations currently employ various
> transparency measures, including open-source firmware, publishing technical documentation, or
> undergoing external audits, but these require investments with unclear returns. This may discourage
> the adoption of transparency, leaving users with limited visibility into system privacy measures.
> Additionally, the lack of standardisation complicates meaningful comparisons between
> implementations. To address these challenges, we propose a three-level conceptual framework
> providing organisations with a practical pathway to incrementally improve Confidential Computing
> transparency. To evaluate whether our transparency framework contributes to an increase in end-user
> trust, we conducted an empirical study with over 800 non-expert participants. The results indicate
> that greater transparency improves user comfort, with participants willing to share various types of
> personal data across different levels of transparency. The study also reveals misconceptions about
> transparency, highlighting the need for clear communication and user education.

## Private-silo collaboration, access control, and provenance

### 30. [PRICURE: Privacy-Preserving Collaborative Inference in a Multi-Party Setting](https://arxiv.org/abs/2102.09751)

- **arXiv:** [2102.09751](https://arxiv.org/abs/2102.09751)
- **Date:** published 2021-02-19
- **Authors:** Ismat Jarin, Birhanu Eshete
- **Categories:** cs.CR, cs.LG
- **Citation:** Jarin, I. & Eshete, B. (2021). PRICURE: Privacy-Preserving Collaborative Inference in a Multi-Party Setting. arXiv preprint. https://arxiv.org/abs/2102.09751v1

**Abstract:**

> When multiple parties that deal with private data aim for a collaborative prediction task such as
> medical image classification, they are often constrained by data protection regulations and lack of
> trust among collaborating parties. If done in a privacy-preserving manner, predictive analytics can
> benefit from the collective prediction capability of multiple parties holding complementary datasets
> on the same machine learning task. This paper presents PRICURE, a system that combines complementary
> strengths of secure multi-party computation (SMPC) and differential privacy (DP) to enable privacy-
> preserving collaborative prediction among multiple model owners. SMPC enables secret-sharing of
> private models and client inputs with non-colluding secure servers to compute predictions without
> leaking model parameters and inputs. DP masks true prediction results via noisy aggregation so as to
> deter a semi-honest client who may mount membership inference attacks. We evaluate PRICURE on neural
> networks across four datasets including benchmark medical image classification datasets. Our results
> suggest PRICURE guarantees privacy for tens of model owners and clients with acceptable accuracy
> loss. We also show that DP reduces membership inference attack exposure without hurting accuracy.

### 31. [Seven Security Challenges That Must be Solved in Cross-domain Multi-agent LLM Systems](https://arxiv.org/abs/2505.23847)

- **arXiv:** [2505.23847](https://arxiv.org/abs/2505.23847)
- **Date:** published 2025-05-28; updated 2025-07-15
- **Authors:** Ronny Ko, Jiseong Jeong, Shuyuan Zheng, Chuan Xiao, Tae-Wan Kim, Makoto Onizuka, Won-Yong Shin
- **Categories:** cs.CR, cs.AI
- **Citation:** Ko, R., Jeong, J., Zheng, S., Xiao, C., Kim, T., Onizuka, M., & Shin, W. (2025). Seven Security Challenges That Must be Solved in Cross-domain Multi-agent LLM Systems. arXiv preprint. https://arxiv.org/abs/2505.23847v3

**Abstract:**

> Large language models (LLMs) are rapidly evolving into autonomous agents that cooperate across
> organizational boundaries, enabling joint disaster response, supply-chain optimization, and other
> tasks that demand decentralized expertise without surrendering data ownership. Yet, cross-domain
> collaboration shatters the unified trust assumptions behind current alignment and containment
> techniques. An agent benign in isolation may, when receiving messages from an untrusted peer, leak
> secrets or violate policy, producing risks driven by emergent multi-agent dynamics rather than
> classical software bugs. This position paper maps the security agenda for cross-domain multi-agent
> LLM systems. We introduce seven categories of novel security challenges, for each of which we also
> present plausible attacks, security evaluation metrics, and future research guidelines.

### 32. [A Vision for Access Control in LLM-based Agent Systems](https://arxiv.org/abs/2510.11108)

- **arXiv:** [2510.11108](https://arxiv.org/abs/2510.11108)
- **Date:** published 2025-10-13; updated 2025-10-19
- **Authors:** Xinfeng Li, Dong Huang, Jie Li, Hongyi Cai, Zhenhong Zhou, Wei Dong, XiaoFeng Wang, Yang Liu
- **Categories:** cs.MA, cs.AI, cs.CR
- **Citation:** Li, X., Huang, D., Li, J., Cai, H., Zhou, Z., Dong, W., Wang, X., & Liu, Y. (2025). A Vision for Access Control in LLM-based Agent Systems. arXiv preprint. https://arxiv.org/abs/2510.11108v2

**Abstract:**

> The autonomy and contextual complexity of LLM-based agents render traditional access control (AC)
> mechanisms insufficient. Static, rule-based systems designed for predictable environments are
> fundamentally ill-equipped to manage the dynamic information flows inherent in agentic interactions.
> This position paper argues for a paradigm shift from binary access control to a more sophisticated
> model of information governance, positing that the core challenge is not merely about permission,
> but about governing the flow of information. We introduce Agent Access Control (AAC), a novel
> framework that reframes AC as a dynamic, context-aware process of information flow governance. AAC
> operates on two core modules: (1) multi-dimensional contextual evaluation, which assesses not just
> identity but also relationships, scenarios, and norms; and (2) adaptive response formulation, which
> moves beyond simple allow/deny decisions to shape information through redaction, summarization, and
> paraphrasing. This vision, powered by a dedicated AC reasoning engine, aims to bridge the gap
> between human-like nuanced judgment and scalable Al safety, proposing a new conceptual lens for
> future research in trustworthy agent design.

### 33. [Access control for Data Spaces](https://arxiv.org/abs/2504.13767)

- **arXiv:** [2504.13767](https://arxiv.org/abs/2504.13767)
- **Date:** published 2025-04-18
- **Authors:** Nikos Fotiou, Vasilios A. Siris, George C. Polyzos
- **Categories:** cs.CR
- **DOI:** 10.1109/ICIN64016.2025.10943024
- **Citation:** Fotiou, N., Siris, V. A., & Polyzos, G. C. (2025). Access control for Data Spaces. arXiv preprint. https://arxiv.org/abs/2504.13767v1

**Abstract:**

> Data spaces represent an emerging paradigm that facilitates secure and trusted data exchange through
> foundational elements of data interoperability, sovereignty, and trust. Within a data space, data
> items, potentially owned by different entities, can be interconnected. Concurrently, data consumers
> can execute advanced data lookup operations and subscribe to data-driven events. Achieving fine-
> grained access control without compromising functionality presents a significant challenge. In this
> paper, we design and implement an access control mechanism that ensures continuous evaluation of
> access control policies, is data semantics aware, and supports subscriptions to data events. We
> present a construction where access control policies are stored in a centralized location, which we
> extend to allow data owners to maintain their own Policy Administration Points. This extension
> builds upon W3C Verifiable Credentials.

### 34. [Privacy Preserving Conversion Modeling in Data Clean Room](https://arxiv.org/abs/2505.14959)

- **arXiv:** [2505.14959](https://arxiv.org/abs/2505.14959)
- **Date:** published 2025-05-20
- **Authors:** Kungang Li, Xiangyi Chen, Ling Leng, Jiajing Xu, Jiankai Sun, Behnam Rezaei
- **Categories:** cs.LG, cs.IR
- **DOI:** 10.1145/3640457.3688054
- **Citation:** Li, K., Chen, X., Leng, L., Xu, J., Sun, J., & Rezaei, B. (2025). Privacy Preserving Conversion Modeling in Data Clean Room. arXiv preprint. https://arxiv.org/abs/2505.14959v1

**Abstract:**

> In the realm of online advertising, accurately predicting the conversion rate (CVR) is crucial for
> enhancing advertising efficiency and user satisfaction. This paper addresses the challenge of CVR
> prediction while adhering to user privacy preferences and advertiser requirements. Traditional
> methods face obstacles such as the reluctance of advertisers to share sensitive conversion data and
> the limitations of model training in secure environments like data clean rooms. We propose a novel
> model training framework that enables collaborative model training without sharing sample-level
> gradients with the advertising platform. Our approach introduces several innovative components: (1)
> utilizing batch-level aggregated gradients instead of sample-level gradients to minimize privacy
> risks; (2) applying adapter-based parameter-efficient fine-tuning and gradient compression to reduce
> communication costs; and (3) employing de-biasing techniques to train the model under label
> differential privacy, thereby maintaining accuracy despite privacy-enhanced label perturbations. Our
> experimental results, conducted on industrial datasets, demonstrate that our method achieves
> competitive ROCAUC performance while significantly decreasing communication overhead and complying
> with both advertiser privacy requirements and user privacy choices. This framework establishes a new
> standard for privacy-preserving, high-performance CVR prediction in the digital advertising
> landscape.

### 35. [From Fluent to Verifiable: Claim-Level Auditability for Deep Research Agents](https://arxiv.org/abs/2602.13855)

- **arXiv:** [2602.13855](https://arxiv.org/abs/2602.13855)
- **Date:** published 2026-02-14
- **Authors:** Razeen A Rasheed, Somnath Banerjee, Animesh Mukherjee, Rima Hazra
- **Categories:** cs.AI, cs.IR, cs.MA
- **Citation:** Rasheed, R. A., Banerjee, S., Mukherjee, A., & Hazra, R. (2026). From Fluent to Verifiable: Claim-Level Auditability for Deep Research Agents. arXiv preprint. https://arxiv.org/abs/2602.13855v1

**Abstract:**

> A deep research agent produces a fluent scientific report in minutes; a careful reader then tries to
> verify the main claims and discovers the real cost is not reading, but tracing: which sentence is
> supported by which passage, what was ignored, and where evidence conflicts. We argue that as
> research generation becomes cheap, auditability becomes the bottleneck, and the dominant risk shifts
> from isolated factual errors to scientifically styled outputs whose claim-evidence links are weak,
> missing, or misleading. This perspective proposes claim-level auditability as a first-class design
> and evaluation target for deep research agents, distills recurring long-horizon failure modes
> (objective drift, transient constraints, and unverifiable inference), and introduces the Auditable
> Autonomous Research (AAR) standard, a compact measurement framework that makes auditability testable
> via provenance coverage, provenance soundness, contradiction transparency, and audit effort. We then
> argue for semantic provenance with protocolized validation: persistent, queryable provenance graphs
> that encode claim--evidence relations (including conflicts) and integrate continuous validation
> during synthesis rather than after publication, with practical instrumentation patterns to support
> deployment at scale.

### 36. [AgentGuardian: Learning Access Control Policies to Govern AI Agent Behavior](https://arxiv.org/abs/2601.10440)

- **arXiv:** [2601.10440](https://arxiv.org/abs/2601.10440)
- **Date:** published 2026-01-15
- **Authors:** Nadya Abaev, Denis Klimov, Gerard Levinov, David Mimran, Yuval Elovici, Asaf Shabtai
- **Categories:** cs.CR, cs.AI, cs.LG
- **Citation:** Abaev, N., Klimov, D., Levinov, G., Mimran, D., Elovici, Y., & Shabtai, A. (2026). AgentGuardian: Learning Access Control Policies to Govern AI Agent Behavior. arXiv preprint. https://arxiv.org/abs/2601.10440v1

**Abstract:**

> Artificial intelligence (AI) agents are increasingly used in a variety of domains to automate tasks,
> interact with users, and make decisions based on data inputs. Ensuring that AI agents perform only
> authorized actions and handle inputs appropriately is essential for maintaining system integrity and
> preventing misuse. In this study, we introduce the AgentGuardian, a novel security framework that
> governs and protects AI agent operations by enforcing context-aware access-control policies. During
> a controlled staging phase, the framework monitors execution traces to learn legitimate agent
> behaviors and input patterns. From this phase, it derives adaptive policies that regulate tool calls
> made by the agent, guided by both real-time input context and the control flow dependencies of
> multi-step agent actions. Evaluation across two real-world AI agent applications demonstrates that
> AgentGuardian effectively detects malicious or misleading inputs while preserving normal agent
> functionality. Moreover, its control-flow-based governance mechanism mitigates hallucination-driven
> errors and other orchestration-level malfunctions.

### 37. [ARBITER: AI-Driven Filtering for Role-Based Access Control](https://arxiv.org/abs/2512.20535)

- **arXiv:** [2512.20535](https://arxiv.org/abs/2512.20535)
- **Date:** published 2025-12-23
- **Authors:** Michele Lorenzo, Idilio Drago, Dario Salvadori, Fabio Romolo Vayr
- **Categories:** cs.CR
- **Citation:** Lorenzo, M., Drago, I., Salvadori, D., & Vayr, F. R. (2025). ARBITER: AI-Driven Filtering for Role-Based Access Control. arXiv preprint. https://arxiv.org/abs/2512.20535v1

**Abstract:**

> Role-Based Access Control (RBAC) struggles to adapt to dynamic enterprise environments with
> documents that contain information that cannot be disclosed to specific user groups. As these
> documents are used by LLM-driven systems (e.g., in RAG) the problem is exacerbated as LLMs can leak
> sensitive data due to prompt truncation, classification errors, or loss of system context. We
> introduce \our, a system designed to provide RBAC in RAG systems. \our implements layered
> input/output validation, role-aware retrieval, and post-generation fact-checking. Unlike traditional
> RBAC approaches that rely on fine-tuned classifiers, \our uses LLMs operating in few-shot settings
> with prompt-based steering for rapid deployment and role updates. We evaluate the approach on 389
> queries using a synthetic dataset. Experimental results show 85\% accuracy and 89\% F1-score in
> query filtering, close to traditional RBAC solutions. Results suggest that practical RBAC deployment
> on RAG systems is approaching the maturity level needed for dynamic enterprise environments.

### 38. [Adaptive Accountability in Networked MAS: Tracing and Mitigating Emergent Norms at Scale](https://arxiv.org/abs/2512.18561)

- **arXiv:** [2512.18561](https://arxiv.org/abs/2512.18561)
- **Date:** published 2025-12-21; updated 2026-03-19
- **Authors:** Saad Alqithami
- **Categories:** cs.MA, cs.AI
- **Citation:** Alqithami, S. (2025). Adaptive Accountability in Networked MAS: Tracing and Mitigating Emergent Norms at Scale. arXiv preprint. https://arxiv.org/abs/2512.18561v3

**Abstract:**

> Large-scale networked multi-agent systems increasingly underpin critical infrastructure, yet their
> collective behavior can drift toward undesirable emergent norms such as collusion, resource
> hoarding, and implicit unfairness. We present the Adaptive Accountability Framework (AAF), an end-
> to-end runtime layer that (i) records cryptographically verifiable interaction provenance, (ii)
> detects distributional change points in streaming traces, (iii) attributes responsibility via a
> causal influence graph, and (iv) applies cost-bounded interventions-reward shaping and targeted
> policy patching-to steer the system back toward compliant behavior. We establish a bounded-
> compromise guarantee: if the expected cost of intervention exceeds an adversary's expected payoff,
> the long-run fraction of compromised interactions converges to a value strictly below one. We
> evaluate AAF in a large-scale factorial simulation suite (87,480 runs across two tasks; up to 100
> agents plus a 500-agent scaling sweep; full and partial observability; Byzantine rates up to 10%; 10
> seeds per regime). Across 324 regimes, AAF lowers the executed compromise ratio relative to a
> Proximal Policy Optimization baseline in 96% of regimes (median relative reduction 11.9%) while
> preserving social welfare (median change 0.4%). Under adversarial injections, AAF detects norm
> violations with a median delay of 71 steps (interquartile range 39-177) and achieves a mean top-
> ranked attribution accuracy of 0.97 at 10% Byzantine rate.

### 39. [Federated Learning: A Survey on Privacy-Preserving Collaborative Intelligence](https://arxiv.org/abs/2504.17703)

- **arXiv:** [2504.17703](https://arxiv.org/abs/2504.17703)
- **Date:** published 2025-04-24; updated 2026-03-05
- **Authors:** Ratun Rahman
- **Categories:** cs.LG, cs.AI
- **Citation:** Rahman, R. (2025). Federated Learning: A Survey on Privacy-Preserving Collaborative Intelligence. arXiv preprint. https://arxiv.org/abs/2504.17703v4

**Abstract:**

> Federated Learning (FL) has emerged as a transformative paradigm in the field of distributed machine
> learning, enabling multiple clients such as mobile devices, edge nodes, or organizations to
> collaboratively train a shared global model without the need to centralize sensitive data. This
> decentralized approach addresses growing concerns around data privacy, security, and regulatory
> compliance, making it particularly attractive in domains such as healthcare, finance, and smart IoT
> systems. This survey provides a concise yet comprehensive overview of Federated Learning, beginning
> with its core architecture and communication protocol. We discuss the standard FL lifecycle,
> including local training, model aggregation, and global updates. A particular emphasis is placed on
> key technical challenges such as handling non-IID (non-independent and identically distributed)
> data, mitigating system and hardware heterogeneity, reducing communication overhead, and ensuring
> privacy through mechanisms like differential privacy and secure aggregation. Furthermore, we examine
> emerging trends in FL research, including personalized FL, cross-device versus cross-silo settings,
> and integration with other paradigms such as reinforcement learning and quantum computing. We also
> highlight real-world applications and summarize benchmark datasets and evaluation metrics commonly
> used in FL research. Finally, we outline open research problems and future directions to guide the
> development of scalable, efficient, and trustworthy FL systems.

### 40. [OPUS-VFL: Incentivizing Optimal Privacy-Utility Tradeoffs in Vertical Federated Learning](https://arxiv.org/abs/2504.15995)

- **arXiv:** [2504.15995](https://arxiv.org/abs/2504.15995)
- **Date:** published 2025-04-22; updated 2026-03-18
- **Authors:** Sindhuja Madabushi, Ahmad Faraz Khan, Haider Ali, Jin-Hee Cho
- **Categories:** cs.LG, cs.AI
- **Citation:** Madabushi, S., Khan, A. F., Ali, H., & Cho, J. (2025). OPUS-VFL: Incentivizing Optimal Privacy-Utility Tradeoffs in Vertical Federated Learning. arXiv preprint. https://arxiv.org/abs/2504.15995v2

**Abstract:**

> Vertical Federated Learning (VFL) enables organizations with disjoint feature spaces but shared user
> bases to collaboratively train models without sharing raw data. However, existing VFL systems face
> critical limitations: they often lack effective incentive mechanisms, struggle to balance privacy-
> utility tradeoffs, and fail to accommodate clients with heterogeneous resource capabilities. These
> challenges hinder meaningful participation, degrade model performance, and limit practical
> deployment. To address these issues, we propose OPUS-VFL, an Optimal Privacy-Utility tradeoff
> Strategy for VFL. OPUS-VFL introduces a novel, privacy-aware incentive mechanism that rewards
> clients based on a principled combination of model contribution, privacy preservation, and resource
> investment. It employs a lightweight leave-one-out (LOO) strategy to quantify feature importance per
> client, and integrates an adaptive differential privacy mechanism that enables clients to
> dynamically calibrate noise levels to optimize their individual utility. Our framework is designed
> to be scalable, budget-balanced, and robust to inference and poisoning attacks. Extensive
> experiments on benchmark datasets (MNIST, CIFAR-10, and CIFAR-100) demonstrate that OPUS-VFL
> significantly outperforms state-of-the-art VFL baselines in both efficiency and robustness. It
> reduces label inference attack success rates by up to 20%, increases feature inference
> reconstruction error (MSE) by over 30%, and achieves up to 25% higher incentives for clients that
> contribute meaningfully while respecting privacy and cost constraints. These results highlight the
> practicality and innovation of OPUS-VFL as a secure, fair, and performance-driven solution for real-
> world VFL.

## Shapley, credit assignment, and data markets

### 41. [Towards Efficient Data Valuation Based on the Shapley Value](https://arxiv.org/abs/1902.10275)

- **arXiv:** [1902.10275](https://arxiv.org/abs/1902.10275)
- **Date:** published 2019-02-27; updated 2020-08-17
- **Authors:** Ruoxi Jia, David Dao, Boxin Wang, Frances Ann Hubis, Nick Hynes, Nezihe Merve Gurel, Bo Li, Ce Zhang, Dawn Song, Costas Spanos
- **Categories:** cs.LG, stat.ML
- **Citation:** Jia, R., Dao, D., Wang, B., Hubis, F. A., Hynes, N., Gurel, N. M., Li, B., Zhang, C., Song, D., & Spanos, C. (2019). Towards Efficient Data Valuation Based on the Shapley Value. arXiv preprint. https://arxiv.org/abs/1902.10275v3

**Abstract:**

> "How much is my data worth?" is an increasingly common question posed by organizations and
> individuals alike. An answer to this question could allow, for instance, fairly distributing profits
> among multiple data contributors and determining prospective compensation when data breaches happen.
> In this paper, we study the problem of data valuation by utilizing the Shapley value, a popular
> notion of value which originated in coopoerative game theory. The Shapley value defines a unique
> payoff scheme that satisfies many desiderata for the notion of data value. However, the Shapley
> value often requires exponential time to compute. To meet this challenge, we propose a repertoire of
> efficient algorithms for approximating the Shapley value. We also demonstrate the value of each
> training instance for various benchmark datasets.

### 42. [Fair and efficient contribution valuation for vertical federated learning](https://arxiv.org/abs/2201.02658)

- **arXiv:** [2201.02658](https://arxiv.org/abs/2201.02658)
- **Date:** published 2022-01-07; updated 2025-08-21
- **Authors:** Zhenan Fan, Huang Fang, Xinglu Wang, Zirui Zhou, Jian Pei, Michael P. Friedlander, Yong Zhang
- **Categories:** cs.LG
- **Citation:** Fan, Z., Fang, H., Wang, X., Zhou, Z., Pei, J., Friedlander, M. P., & Zhang, Y. (2022). Fair and efficient contribution valuation for vertical federated learning. arXiv preprint. https://arxiv.org/abs/2201.02658v2

**Abstract:**

> Federated learning is an emerging technology for training machine learning models across
> decentralized data sources without sharing data. Vertical federated learning, also known as feature-
> based federated learning, applies to scenarios where data sources have the same sample IDs but
> different feature sets. To ensure fairness among data owners, it is critical to objectively assess
> the contributions from different data sources and compensate the corresponding data owners
> accordingly. The Shapley value is a provably fair contribution valuation metric originating from
> cooperative game theory. However, its straight-forward computation requires extensively retraining a
> model on each potential combination of data sources, leading to prohibitively high communication and
> computation overheads due to multiple rounds of federated learning. To tackle this challenge, we
> propose a contribution valuation metric called vertical federated Shapley value (VerFedSV) based on
> the classic Shapley value. We show that VerFedSV not only satisfies many desirable properties of
> fairness but is also efficient to compute. Moreover, VerFedSV can be adapted to both synchronous and
> asynchronous vertical federated learning algorithms. Both theoretical analysis and extensive
> experimental results demonstrate the fairness, efficiency, adaptability, and effectiveness of
> VerFedSV.

### 43. [Data Valuation for Vertical Federated Learning: A Model-free and Privacy-preserving Method](https://arxiv.org/abs/2112.08364)

- **arXiv:** [2112.08364](https://arxiv.org/abs/2112.08364)
- **Date:** published 2021-12-15; updated 2024-01-04
- **Authors:** Xiao Han, Leye Wang, Junjie Wu, Xiao Fang
- **Categories:** cs.LG, cs.AI
- **Citation:** Han, X., Wang, L., Wu, J., & Fang, X. (2021). Data Valuation for Vertical Federated Learning: A Model-free and Privacy-preserving Method. arXiv preprint. https://arxiv.org/abs/2112.08364v3

**Abstract:**

> Vertical Federated learning (VFL) is a promising paradigm for predictive analytics, empowering an
> organization (i.e., task party) to enhance its predictive models through collaborations with
> multiple data suppliers (i.e., data parties) in a decentralized and privacy-preserving way. Despite
> the fast-growing interest in VFL, the lack of effective and secure tools for assessing the value of
> data owned by data parties hinders the application of VFL in business contexts. In response, we
> propose FedValue, a privacy-preserving, task-specific but model-free data valuation method for VFL,
> which consists of a data valuation metric and a federated computation method. Specifically, we first
> introduce a novel data valuation metric, namely MShapley-CMI. The metric evaluates a data party's
> contribution to a predictive analytics task without the need of executing a machine learning model,
> making it well-suited for real-world applications of VFL. Next, we develop an innovative federated
> computation method that calculates the MShapley-CMI value for each data party in a privacy-
> preserving manner. Extensive experiments conducted on six public datasets validate the efficacy of
> FedValue for data valuation in the context of VFL. In addition, we illustrate the practical utility
> of FedValue with a case study involving federated movie recommendations.

### 44. [GTG-Shapley: Efficient and Accurate Participant Contribution Evaluation in Federated Learning](https://arxiv.org/abs/2109.02053)

- **arXiv:** [2109.02053](https://arxiv.org/abs/2109.02053)
- **Date:** published 2021-09-05
- **Authors:** Zelei Liu, Yuanyuan Chen, Han Yu, Yang Liu, Lizhen Cui
- **Categories:** cs.AI
- **Citation:** Liu, Z., Chen, Y., Yu, H., Liu, Y., & Cui, L. (2021). GTG-Shapley: Efficient and Accurate Participant Contribution Evaluation in Federated Learning. arXiv preprint. https://arxiv.org/abs/2109.02053v1

**Abstract:**

> Federated Learning (FL) bridges the gap between collaborative machine learning and preserving data
> privacy. To sustain the long-term operation of an FL ecosystem, it is important to attract high
> quality data owners with appropriate incentive schemes. As an important building block of such
> incentive schemes, it is essential to fairly evaluate participants' contribution to the performance
> of the final FL model without exposing their private data. Shapley Value (SV)-based techniques have
> been widely adopted to provide fair evaluation of FL participant contributions. However, existing
> approaches incur significant computation costs, making them difficult to apply in practice. In this
> paper, we propose the Guided Truncation Gradient Shapley (GTG-Shapley) approach to address this
> challenge. It reconstructs FL models from gradient updates for SV calculation instead of repeatedly
> training with different combinations of FL participants. In addition, we design a guided Monte Carlo
> sampling approach combined with within-round and between-round truncation to further reduce the
> number of model reconstructions and evaluations required, through extensive experiments under
> diverse realistic data distribution settings. The results demonstrate that GTG-Shapley can closely
> approximate actual Shapley values, while significantly increasing computational efficiency compared
> to the state of the art, especially under non-i.i.d. settings.

### 45. [Differentially Private Shapley Values for Data Evaluation](https://arxiv.org/abs/2206.00511)

- **arXiv:** [2206.00511](https://arxiv.org/abs/2206.00511)
- **Date:** published 2022-06-01
- **Authors:** Lauren Watson, Rayna Andreeva, Hao-Tsung Yang, Rik Sarkar
- **Categories:** cs.LG, cs.CR
- **Citation:** Watson, L., Andreeva, R., Yang, H., & Sarkar, R. (2022). Differentially Private Shapley Values for Data Evaluation. arXiv preprint. https://arxiv.org/abs/2206.00511v1

**Abstract:**

> The Shapley value has been proposed as a solution to many applications in machine learning,
> including for equitable valuation of data. Shapley values are computationally expensive and involve
> the entire dataset. The query for a point's Shapley value can also compromise the statistical
> privacy of other data points. We observe that in machine learning problems such as empirical risk
> minimization, and in many learning algorithms (such as those with uniform stability), a diminishing
> returns property holds, where marginal benefit per data point decreases rapidly with data sample
> size. Based on this property, we propose a new stratified approximation method called the Layered
> Shapley Algorithm. We prove that this method operates on small (O(\polylog(n))) random samples of
> data and small sized ($O(\log n)$) coalitions to achieve the results with guaranteed probabilistic
> accuracy, and can be modified to incorporate differential privacy. Experimental results show that
> the algorithm correctly identifies high-value data points that improve validation accuracy, and that
> the differentially private evaluations preserve approximate ranking of data.

### 46. [Threshold KNN-Shapley: A Linear-Time and Privacy-Friendly Approach to Data Valuation](https://arxiv.org/abs/2308.15709)

- **arXiv:** [2308.15709](https://arxiv.org/abs/2308.15709)
- **Date:** published 2023-08-30; updated 2023-11-26
- **Authors:** Jiachen T. Wang, Yuqing Zhu, Yu-Xiang Wang, Ruoxi Jia, Prateek Mittal
- **Categories:** cs.LG, cs.CR, cs.GT, stat.ML
- **Citation:** Wang, J. T., Zhu, Y., Wang, Y., Jia, R., & Mittal, P. (2023). Threshold KNN-Shapley: A Linear-Time and Privacy-Friendly Approach to Data Valuation. arXiv preprint. https://arxiv.org/abs/2308.15709v2

**Abstract:**

> Data valuation aims to quantify the usefulness of individual data sources in training machine
> learning (ML) models, and is a critical aspect of data-centric ML research. However, data valuation
> faces significant yet frequently overlooked privacy challenges despite its importance. This paper
> studies these challenges with a focus on KNN-Shapley, one of the most practical data valuation
> methods nowadays. We first emphasize the inherent privacy risks of KNN-Shapley, and demonstrate the
> significant technical difficulties in adapting KNN-Shapley to accommodate differential privacy (DP).
> To overcome these challenges, we introduce TKNN-Shapley, a refined variant of KNN-Shapley that is
> privacy-friendly, allowing for straightforward modifications to incorporate DP guarantee (DP-TKNN-
> Shapley). We show that DP-TKNN-Shapley has several advantages and offers a superior privacy-utility
> tradeoff compared to naively privatized KNN-Shapley in discerning data quality. Moreover, even non-
> private TKNN-Shapley achieves comparable performance as KNN-Shapley. Overall, our findings suggest
> that TKNN-Shapley is a promising alternative to KNN-Shapley, particularly for real-world
> applications involving sensitive data.

### 47. [Dealer: End-to-End Data Marketplace with Model-based Pricing](https://arxiv.org/abs/2003.13103)

- **arXiv:** [2003.13103](https://arxiv.org/abs/2003.13103)
- **Date:** published 2020-03-29
- **Authors:** Jinfei Liu
- **Categories:** cs.DB
- **Citation:** Liu, J. (2020). Dealer: End-to-End Data Marketplace with Model-based Pricing. arXiv preprint. https://arxiv.org/abs/2003.13103v1

**Abstract:**

> Data-driven machine learning (ML) has witnessed great successes across a variety of application
> domains. Since ML model training are crucially relied on a large amount of data, there is a growing
> demand for high quality data to be collected for ML model training. However, from data owners'
> perspective, it is risky for them to contribute their data. To incentivize data contribution, it
> would be ideal that their data would be used under their preset restrictions and they get paid for
> their data contribution. In this paper, we take a formal data market perspective and propose the
> first en\textbf{\underline{D}}-to-\textbf{\underline{e}}nd d\textbf{\underline{a}}ta
> marketp\textbf{\underline{l}}ace with mod\textbf{\underline{e}}l-based p\textbf{\underline{r}}icing
> (\emph{Dealer}) towards answering the question: \emph{How can the broker assign value to data owners
> based on their contribution to the models to incentivize more data contribution, and determine
> pricing for a series of models for various model buyers to maximize the revenue with arbitrage-free
> guarantee}. For the former, we introduce a Shapley value-based mechanism to quantify each data
> owner's value towards all the models trained out of the contributed data. For the latter, we design
> a pricing mechanism based on models' privacy parameters to maximize the revenue. More importantly,
> we study how the data owners' data usage restrictions affect market design, which is a striking
> difference of our approach with the existing methods. Furthermore, we show a concrete realization
> DP-\emph{Dealer} which provably satisfies the desired formal properties. Extensive experiments show
> that DP-\emph{Dealer} is efficient and effective.

### 48. [Collaborative Machine Learning Markets with Data-Replication-Robust Payments](https://arxiv.org/abs/1911.09052)

- **arXiv:** [1911.09052](https://arxiv.org/abs/1911.09052)
- **Date:** published 2019-11-08
- **Authors:** Olga Ohrimenko, Shruti Tople, Sebastian Tschiatschek
- **Categories:** cs.GT, cs.LG, stat.ML
- **Citation:** Ohrimenko, O., Tople, S., & Tschiatschek, S. (2019). Collaborative Machine Learning Markets with Data-Replication-Robust Payments. arXiv preprint. https://arxiv.org/abs/1911.09052v1

**Abstract:**

> We study the problem of collaborative machine learning markets where multiple parties can achieve
> improved performance on their machine learning tasks by combining their training data. We discuss
> desired properties for these machine learning markets in terms of fair revenue distribution and
> potential threats, including data replication. We then instantiate a collaborative market for cases
> where parties share a common machine learning task and where parties' tasks are different. Our
> marketplace incentivizes parties to submit high quality training and true validation data. To this
> end, we introduce a novel payment division function that is robust-to-replication and customized
> output models that perform well only on requested machine learning tasks. In experiments, we
> validate the assumptions underlying our theoretical analysis and show that these are approximately
> satisfied for commonly used machine learning models.

### 49. [Proof-of-Contribution-Based Design for Collaborative Machine Learning on Blockchain](https://arxiv.org/abs/2302.14031)

- **arXiv:** [2302.14031](https://arxiv.org/abs/2302.14031)
- **Date:** published 2023-02-27
- **Authors:** Baturalp Buyukates, Chaoyang He, Shanshan Han, Zhiyong Fang, Yupeng Zhang, Jieyi Long, Ali Farahanchi, Salman Avestimehr
- **Categories:** cs.CR, cs.DC, cs.LG
- **Citation:** Buyukates, B., He, C., Han, S., Fang, Z., Zhang, Y., Long, J., Farahanchi, A., & Avestimehr, S. (2023). Proof-of-Contribution-Based Design for Collaborative Machine Learning on Blockchain. arXiv preprint. https://arxiv.org/abs/2302.14031v1

**Abstract:**

> We consider a project (model) owner that would like to train a model by utilizing the local private
> data and compute power of interested data owners, i.e., trainers. Our goal is to design a data
> marketplace for such decentralized collaborative/federated learning applications that simultaneously
> provides i) proof-of-contribution based reward allocation so that the trainers are compensated based
> on their contributions to the trained model; ii) privacy-preserving decentralized model training by
> avoiding any data movement from data owners; iii) robustness against malicious parties (e.g.,
> trainers aiming to poison the model); iv) verifiability in the sense that the integrity, i.e.,
> correctness, of all computations in the data market protocol including contribution assessment and
> outlier detection are verifiable through zero-knowledge proofs; and v) efficient and universal
> design. We propose a blockchain-based marketplace design to achieve all five objectives mentioned
> above. In our design, we utilize a distributed storage infrastructure and an aggregator aside from
> the project owner and the trainers. The aggregator is a processing node that performs certain
> computations, including assessing trainer contributions, removing outliers, and updating hyper-
> parameters. We execute the proposed data market through a blockchain smart contract. The deployed
> smart contract ensures that the project owner cannot evade payment, and honest trainers are rewarded
> based on their contributions at the end of training. Finally, we implement the building blocks of
> the proposed data market and demonstrate their applicability in practical scenarios through
> extensive experiments.

### 50. [Reliable and Private Utility Signaling for Data Markets](https://arxiv.org/abs/2511.07975)

- **arXiv:** [2511.07975](https://arxiv.org/abs/2511.07975)
- **Date:** published 2025-11-11
- **Authors:** Li Peng, Jiayao Zhang, Yihang Wu, Weiran Liu, Jinfei Liu, Zheng Yan, Kui Ren, Lei Zhang, Lin Qu
- **Categories:** cs.GT, cs.AI
- **Citation:** Peng, L., Zhang, J., Wu, Y., Liu, W., Liu, J., Yan, Z., Ren, K., Zhang, L., & Qu, L. (2025). Reliable and Private Utility Signaling for Data Markets. arXiv preprint. https://arxiv.org/abs/2511.07975v1

**Abstract:**

> The explosive growth of data has highlighted its critical role in driving economic growth through
> data marketplaces, which enable extensive data sharing and access to high-quality datasets. To
> support effective trading, signaling mechanisms provide participants with information about data
> products before transactions, enabling informed decisions and facilitating trading. However, due to
> the inherent free-duplication nature of data, commonly practiced signaling methods face a dilemma
> between privacy and reliability, undermining the effectiveness of signals in guiding decision-
> making. To address this, this paper explores the benefits and develops a non-TCP-based construction
> for a desirable signaling mechanism that simultaneously ensures privacy and reliability. We begin by
> formally defining the desirable utility signaling mechanism and proving its ability to prevent
> suboptimal decisions for both participants and facilitate informed data trading. To design a
> protocol to realize its functionality, we propose leveraging maliciously secure multi-party
> computation (MPC) to ensure the privacy and robustness of signal computation and introduce an MPC-
> based hash verification scheme to ensure input reliability. In multi-seller scenarios requiring fair
> data valuation, we further explore the design and optimization of the MPC-based KNN-Shapley method
> with improved efficiency. Rigorous experiments demonstrate the efficiency and practicality of our
> approach.

### 51. [Rethinking Data Value: Asymmetric Data Shapley for Structure-Aware Valuation in Data Markets and Machine Learning Pipelines](https://arxiv.org/abs/2511.12863)

- **arXiv:** [2511.12863](https://arxiv.org/abs/2511.12863)
- **Date:** published 2025-11-17
- **Authors:** Xi Zheng, Yinghui Huang, Xiangyu Chang, Ruoxi Jia, Yong Tan
- **Categories:** cs.GT
- **Citation:** Zheng, X., Huang, Y., Chang, X., Jia, R., & Tan, Y. (2025). Rethinking Data Value: Asymmetric Data Shapley for Structure-Aware Valuation in Data Markets and Machine Learning Pipelines. arXiv preprint. https://arxiv.org/abs/2511.12863v1

**Abstract:**

> Rigorous valuation of individual data sources is critical for fair compensation in data markets,
> informed data acquisition, and transparent development of ML/AI models. Classical Data Shapley (DS)
> provides a essential axiomatic framework for data valuation but is constrained by its symmetry axiom
> that assumes interchangeability of data sources. This assumption fails to capture the directional
> and temporal dependencies prevalent in modern ML/AI workflows, including the reliance of duplicated
> or augmented data on original sources and the order-specific contributions in sequential pipelines
> such as federated learning and multi-stage LLM fine tuning. To address these limitations, we
> introduce Asymmetric Data Shapley (ADS), a structure-aware data valuation framework for modern ML/AI
> pipelines. ADS relaxes symmetry by averaging marginal contributions only over permutations
> consistent with an application-specific ordering of data groups. It preserves efficiency and
> linearity, maintains within group symmetry and directional precedence across groups, and reduces to
> DS when the ordering collapses to a single group. We develop two complementary computational
> procedures for ADS: (i) a Monte Carlo estimator (MC-ADS) with finite-sample accuracy guarantees, and
> (ii) a k-nearest neighbor surrogate (KNN-ADS) that is exact and efficient for KNN predictors. Across
> representative settings with directional and temporal dependence, ADS consistently outperforms
> benchmark methods by distinguishing novel from redundant contributions and respecting the sequential
> nature of training. These results establish ADS as a principled and practical approach to equitable
> data valuation in data markets and complex ML/AI pipelines.

### 52. [Variance reduced Shapley value estimation for trustworthy data valuation](https://arxiv.org/abs/2210.16835)

- **arXiv:** [2210.16835](https://arxiv.org/abs/2210.16835)
- **Date:** published 2022-10-30; updated 2023-05-22
- **Authors:** Mengmeng Wu, Ruoxi Jia, Changle Lin, Wei Huang, Xiangyu Chang
- **Categories:** stat.ML, cs.LG
- **Citation:** Wu, M., Jia, R., Lin, C., Huang, W., & Chang, X. (2022). Variance reduced Shapley value estimation for trustworthy data valuation. arXiv preprint. https://arxiv.org/abs/2210.16835v5

**Abstract:**

> Data valuation, especially quantifying data value in algorithmic prediction and decision-making, is
> a fundamental problem in data trading scenarios. The most widely used method is to define the data
> Shapley and approximate it by means of the permutation sampling algorithm. To make up for the large
> estimation variance of the permutation sampling that hinders the development of the data
> marketplace, we propose a more robust data valuation method using stratified sampling, named
> variance reduced data Shapley (VRDS for short). We theoretically show how to stratify, how many
> samples are taken at each stratum, and the sample complexity analysis of VRDS. Finally, the
> effectiveness of VRDS is illustrated in different types of datasets and data removal applications.

### 53. [2D-Shapley: A Framework for Fragmented Data Valuation](https://arxiv.org/abs/2306.10473)

- **arXiv:** [2306.10473](https://arxiv.org/abs/2306.10473)
- **Date:** published 2023-06-18; updated 2023-07-27
- **Authors:** Zhihong Liu, Hoang Anh Just, Xiangyu Chang, Xi Chen, Ruoxi Jia
- **Categories:** cs.LG
- **Citation:** Liu, Z., Just, H. A., Chang, X., Chen, X., & Jia, R. (2023). 2D-Shapley: A Framework for Fragmented Data Valuation. arXiv preprint. https://arxiv.org/abs/2306.10473v2

**Abstract:**

> Data valuation -- quantifying the contribution of individual data sources to certain predictive
> behaviors of a model -- is of great importance to enhancing the transparency of machine learning and
> designing incentive systems for data sharing. Existing work has focused on evaluating data sources
> with the shared feature or sample space. How to valuate fragmented data sources of which each only
> contains partial features and samples remains an open question. We start by presenting a method to
> calculate the counterfactual of removing a fragment from the aggregated data matrix. Based on the
> counterfactual calculation, we further propose 2D-Shapley, a theoretical framework for fragmented
> data valuation that uniquely satisfies some appealing axioms in the fragmented data context.
> 2D-Shapley empowers a range of new use cases, such as selecting useful data fragments, providing
> interpretation for sample-wise data values, and fine-grained data issue diagnosis.

### 54. [Data Shapley in One Training Run](https://arxiv.org/abs/2406.11011)

- **arXiv:** [2406.11011](https://arxiv.org/abs/2406.11011)
- **Date:** published 2024-06-16; updated 2025-06-07
- **Authors:** Jiachen T. Wang, Prateek Mittal, Dawn Song, Ruoxi Jia
- **Categories:** cs.LG, cs.CL, stat.ML
- **Citation:** Wang, J. T., Mittal, P., Song, D., & Jia, R. (2024). Data Shapley in One Training Run. arXiv preprint. https://arxiv.org/abs/2406.11011v3

**Abstract:**

> Data Shapley provides a principled framework for attributing data's contribution within machine
> learning contexts. However, existing approaches require re-training models on different data
> subsets, which is computationally intensive, foreclosing their application to large-scale models.
> Furthermore, they produce the same attribution score for any models produced by running the learning
> algorithm, meaning they cannot perform targeted attribution towards a specific model obtained from a
> single run of the algorithm. This paper introduces In-Run Data Shapley, which addresses these
> limitations by offering scalable data attribution for a target model of interest. In its most
> efficient implementation, our technique incurs negligible additional runtime compared to standard
> model training. This dramatic efficiency improvement makes it possible to perform data attribution
> for the foundation model pretraining stage for the first time. We present several case studies that
> offer fresh insights into pretraining data's contribution and discuss their implications for
> copyright in generative AI and pretraining data curation.

### 55. [Mechanism for Collaborative Federated Learning: Pitfalls of Shapley Values](https://arxiv.org/abs/2403.04753)

- **arXiv:** [2403.04753](https://arxiv.org/abs/2403.04753)
- **Date:** published 2024-03-07; updated 2026-03-21
- **Authors:** Meng Qi, Mingxi Zhu
- **Categories:** cs.GT
- **Citation:** Qi, M. & Zhu, M. (2024). Mechanism for Collaborative Federated Learning: Pitfalls of Shapley Values. arXiv preprint. https://arxiv.org/abs/2403.04753v2

**Abstract:**

> This paper investigates the impact of mechanism design on collaborative learning systems enabled by
> federated learning (FL). We propose a multi-action collaborative federated learning (MCFL)
> framework, capturing the interplay between agent strategies, platform mechanisms, and FL algorithms
> --a "three-body problem" in collaborative learning. This work demonstrates how the convergence rate
> and computational efficiency of FL are endogenously determined by the agent participation
> equilibrium that is induced by the mechanism. By doing so, we establish a direct link between
> incentive design in collaborative learning systems and the performance of the underlying
> optimization algorithms, a connection that has been largely overlooked in the existing literature.
> Specifically, we characterize the equilibrium of agent participation under two prominent mechanisms:
> the Shapley Value (SV) and Marginal Contribution (MC) mechanisms. Although SV is fair in surplus
> allocation and budget balanced, it has a vital pitfall: agents are incentivized to split their data
> across newly created fake identities. This is critical especially in the MCFL setting as it leads to
> slow convergence of FL optimization, which increases the number of required
> synchronization/communication rounds even when the per-round cost is fixed. In contrast, while MC is
> not budget-balanced, it is robust to such strategic manipulation and is able to induce an
> equilibrium that maximizes the MCFL system efficiency. Overall, our study lays a foundation for
> jointly designing incentives and algorithms in MCFL systems. We provide insights on pitfalls of SV:
> it induces a system equilibrium that leads to tremendous training cost and slower convergence,
> ultimately undermining the effectiveness of collaborative learning.

### 56. [A Comprehensive Survey of Incentive Mechanism for Federated Learning](https://arxiv.org/abs/2106.15406)

- **arXiv:** [2106.15406](https://arxiv.org/abs/2106.15406)
- **Date:** published 2021-06-27
- **Authors:** Rongfei Zeng, Chao Zeng, Xingwei Wang, Bo Li, Xiaowen Chu
- **Categories:** cs.LG, cs.GT
- **Citation:** Zeng, R., Zeng, C., Wang, X., Li, B., & Chu, X. (2021). A Comprehensive Survey of Incentive Mechanism for Federated Learning. arXiv preprint. https://arxiv.org/abs/2106.15406v1

**Abstract:**

> Federated learning utilizes various resources provided by participants to collaboratively train a
> global model, which potentially address the data privacy issue of machine learning. In such
> promising paradigm, the performance will be deteriorated without sufficient training data and other
> resources in the learning process. Thus, it is quite crucial to inspire more participants to
> contribute their valuable resources with some payments for federated learning. In this paper, we
> present a comprehensive survey of incentive schemes for federate learning. Specifically, we identify
> the incentive problem in federated learning and then provide a taxonomy for various schemes.
> Subsequently, we summarize the existing incentive mechanisms in terms of the main techniques, such
> as Stackelberg game, auction, contract theory, Shapley value, reinforcement learning, blockchain. By
> reviewing and comparing some impressive results, we figure out three directions for the future
> study.

## Decentralized AI, agent economies, and verifiable inference markets

### 57. [Decentralized & Collaborative AI on Blockchain](https://arxiv.org/abs/1907.07247)

- **arXiv:** [1907.07247](https://arxiv.org/abs/1907.07247)
- **Date:** published 2019-07-16
- **Authors:** Justin D. Harris, Bo Waggoner
- **Categories:** cs.CR, cs.AI, cs.HC
- **DOI:** 10.1109/Blockchain.2019.00057
- **Citation:** Harris, J. D. & Waggoner, B. (2019). Decentralized & Collaborative AI on Blockchain. arXiv preprint. https://arxiv.org/abs/1907.07247v1

**Abstract:**

> Machine learning has recently enabled large advances in artificial intelligence, but these tend to
> be highly centralized. The large datasets required are generally proprietary; predictions are often
> sold on a per-query basis; and published models can quickly become out of date without effort to
> acquire more data and re-train them. We propose a framework for participants to collaboratively
> build a dataset and use smart contracts to host a continuously updated model. This model will be
> shared publicly on a blockchain where it can be free to use for inference. Ideal learning problems
> include scenarios where a model is used many times for similar input such as personal assistants,
> playing games, recommender systems, etc. In order to maintain the model's accuracy with respect to
> some test set we propose both financial and non-financial (gamified) incentive structures for
> providing good data. A free and open source implementation for the Ethereum blockchain is provided
> at https://github.com/microsoft/0xDeCA10B.

### 58. [Ownership preserving AI Market Places using Blockchain](https://arxiv.org/abs/2001.09011)

- **arXiv:** [2001.09011](https://arxiv.org/abs/2001.09011)
- **Date:** published 2020-01-18
- **Authors:** Nishant Baranwal Somy, Kalapriya Kannan, Vijay Arya, Sandeep Hans, Abhishek Singh, Pranay Lohia, Sameep Mehta
- **Categories:** cs.DC, cs.CR
- **DOI:** 10.1109/Blockchain.2019.00029
- **Citation:** Somy, N. B., Kannan, K., Arya, V., Hans, S., Singh, A., Lohia, P., & Mehta, S. (2020). Ownership preserving AI Market Places using Blockchain. arXiv preprint. https://arxiv.org/abs/2001.09011v1

**Abstract:**

> We present a blockchain based system that allows data owners, cloud vendors, and AI developers to
> collaboratively train machine learning models in a trustless AI marketplace. Data is a highly valued
> digital asset and central to deriving business insights. Our system enables data owners to retain
> ownership and privacy of their data, while still allowing AI developers to leverage the data for
> training. Similarly, AI developers can utilize compute resources from cloud vendors without loosing
> ownership or privacy of their trained models. Our system protocols are set up to incentivize all
> three entities - data owners, cloud vendors, and AI developers to truthfully record their actions on
> the distributed ledger, so that the blockchain system provides verifiable evidence of wrongdoing and
> dispute resolution. Our system is implemented on the Hyperledger Fabric and can provide a viable
> alternative to centralized AI systems that do not guarantee data or model privacy. We present
> experimental performance results that demonstrate the latency and throughput of its transactions
> under different network configurations where peers on the blockchain may be spread across different
> datacenters and geographies. Our results indicate that the proposed solution scales well to large
> number of data and model owners and can train up to 70 models per second on a 12-peer non optimized
> blockchain network and roughly 30 models per second in a 24 peer network.

### 59. [PredictChain: Empowering Collaboration and Data Accessibility for AI in a Decentralized Blockchain-based Marketplace](https://arxiv.org/abs/2307.15168)

- **arXiv:** [2307.15168](https://arxiv.org/abs/2307.15168)
- **Date:** published 2023-07-27
- **Authors:** Matthew T. Pisano, Connor J. Patterson, Oshani Seneviratne
- **Categories:** cs.LG, cs.DC
- **Citation:** Pisano, M. T., Patterson, C. J., & Seneviratne, O. (2023). PredictChain: Empowering Collaboration and Data Accessibility for AI in a Decentralized Blockchain-based Marketplace. arXiv preprint. https://arxiv.org/abs/2307.15168v1

**Abstract:**

> Limited access to computing resources and training data poses significant challenges for individuals
> and groups aiming to train and utilize predictive machine learning models. Although numerous
> publicly available machine learning models exist, they are often unhosted, necessitating end-users
> to establish their computational infrastructure. Alternatively, these models may only be accessible
> through paid cloud-based mechanisms, which can prove costly for general public utilization.
> Moreover, model and data providers require a more streamlined approach to track resource usage and
> capitalize on subsequent usage by others, both financially and otherwise. An effective mechanism is
> also lacking to contribute high-quality data for improving model performance. We propose a
> blockchain-based marketplace called "PredictChain" for predictive machine-learning models to address
> these issues. This marketplace enables users to upload datasets for training predictive machine
> learning models, request model training on previously uploaded datasets, or submit queries to
> trained models. Nodes within the blockchain network, equipped with available computing resources,
> will operate these models, offering a range of archetype machine learning models with varying
> characteristics, such as cost, speed, simplicity, power, and cost-effectiveness. This decentralized
> approach empowers users to develop improved models accessible to the public, promotes data sharing,
> and reduces reliance on centralized cloud providers.

### 60. [A Marketplace for Trading AI Models based on Blockchain and Incentives for IoT Data](https://arxiv.org/abs/2112.02870)

- **arXiv:** [2112.02870](https://arxiv.org/abs/2112.02870)
- **Date:** published 2021-12-06
- **Authors:** Lam Duc Nguyen, Shashi Raj Pandey, Soret Beatriz, Arne Broering, Petar Popovski
- **Categories:** cs.LG, cs.DC
- **Citation:** Nguyen, L. D., Pandey, S. R., Beatriz, S., Broering, A., & Popovski, P. (2021). A Marketplace for Trading AI Models based on Blockchain and Incentives for IoT Data. arXiv preprint. https://arxiv.org/abs/2112.02870v1

**Abstract:**

> As Machine Learning (ML) models are becoming increasingly complex, one of the central challenges is
> their deployment at scale, such that companies and organizations can create value through Artificial
> Intelligence (AI). An emerging paradigm in ML is a federated approach where the learning model is
> delivered to a group of heterogeneous agents partially, allowing agents to train the model locally
> with their own data. However, the problem of valuation of models, as well the questions of
> incentives for collaborative training and trading of data/models, have received limited treatment in
> the literature. In this paper, a new ecosystem of ML model trading over a trusted Blockchain-based
> network is proposed. The buyer can acquire the model of interest from the ML market, and interested
> sellers spend local computations on their data to enhance that model's quality. In doing so, the
> proportional relation between the local data and the quality of trained models is considered, and
> the valuations of seller's data in training the models are estimated through the distributed Data
> Shapley Value (DSV). At the same time, the trustworthiness of the entire trading process is provided
> by the distributed Ledger Technology (DLT). Extensive experimental evaluation of the proposed
> approach shows a competitive run-time performance, with a 15\% drop in the cost of execution, and
> fairness in terms of incentives for the participants.

### 61. [SoK: Blockchain-Based Decentralized AI (DeAI)](https://arxiv.org/abs/2411.17461)

- **arXiv:** [2411.17461](https://arxiv.org/abs/2411.17461)
- **Date:** published 2024-11-26; updated 2026-02-08
- **Authors:** Elizabeth Lui, Rui Sun, Vatsal Shah, Xihan Xiong, Jiahao Sun, Davide Crapis, William Knottenbelt, Zhipeng Wang
- **Categories:** cs.LG, cs.AI, cs.CR
- **Citation:** Lui, E., Sun, R., Shah, V., Xiong, X., Sun, J., Crapis, D., Knottenbelt, W., & Wang, Z. (2024). SoK: Blockchain-Based Decentralized AI (DeAI). arXiv preprint. https://arxiv.org/abs/2411.17461v5

**Abstract:**

> Centralization enhances the efficiency of Artificial Intelligence (AI) but also introduces critical
> challenges, including single points of failure, inherent biases, data privacy risks, and scalability
> limitations. To address these issues, blockchain-based Decentralized Artificial Intelligence (DeAI)
> has emerged as a promising paradigm that leverages decentralization and transparency to improve the
> trustworthiness of AI systems. Despite rapid adoption in industry, the academic community lacks a
> systematic analysis of DeAI's technical foundations, opportunities, and challenges. This work
> presents the first Systematization of Knowledge (SoK) on DeAI, offering a formal definition, a
> taxonomy of existing solutions based on the AI lifecycle, and an in-depth investigation of the roles
> of blockchain in enabling secure and incentive-compatible collaboration. We further review security
> risks across the DeAI lifecycle and empirically evaluate representative mitigation techniques.
> Finally, we highlight open research challenges and future directions for advancing blockchain-based
> DeAI.

### 62. [Decentralized AI: Permissionless LLM Inference on POKT Network](https://arxiv.org/abs/2405.20450)

- **arXiv:** [2405.20450](https://arxiv.org/abs/2405.20450)
- **Date:** published 2024-05-30
- **Authors:** Daniel Olshansky, Ramiro Rodriguez Colmeiro, Bowen Li
- **Categories:** cs.DC, cs.AI
- **Citation:** Olshansky, D., Colmeiro, R. R., & Li, B. (2024). Decentralized AI: Permissionless LLM Inference on POKT Network. arXiv preprint. https://arxiv.org/abs/2405.20450v1

**Abstract:**

> POKT Network's decentralized Remote Procedure Call (RPC) infrastructure, surpassing 740 billion
> requests since launching on MainNet in 2020, is well-positioned to extend into providing AI
> inference services with minimal design or implementation modifications. This litepaper illustrates
> how the network's open-source and permissionless design aligns incentives among model researchers,
> hardware operators, API providers and users whom we term model Sources, Suppliers, Gateways and
> Applications respectively. Through its Relay Mining algorithm, POKT creates a transparent
> marketplace where costs and earnings directly reflect cryptographically verified usage. This
> decentralized framework offers large model AI researchers a new avenue to disseminate their work and
> generate revenue without the complexities of maintaining infrastructure or building end-user
> products. Supply scales naturally with demand, as evidenced in recent years and the protocol's free
> market dynamics. POKT Gateways facilitate network growth, evolution, adoption, and quality by acting
> as application-facing load balancers, providing value-added features without managing LLM nodes
> directly. This vertically decoupled network, battle tested over several years, is set up to
> accelerate the adoption, operation, innovation and financialization of open-source models. It is the
> first mature permissionless network whose quality of service competes with centralized entities set
> up to provide application grade inference.

### 63. [PolyLink: A Blockchain Based Decentralized Edge AI Platform for LLM Inference](https://arxiv.org/abs/2510.02395)

- **arXiv:** [2510.02395](https://arxiv.org/abs/2510.02395)
- **Date:** published 2025-10-01
- **Authors:** Hongbo Liu, Jiannong Cao, Bo Yang, Dongbin Bai, Yinfeng Cao, Xiaoming Shen, Yinan Zhang, Jinwen Liang, Shan Jiang, Mingjin Zhang
- **Categories:** cs.CR, cs.DC
- **Citation:** Liu, H., Cao, J., Yang, B., Bai, D., Cao, Y., Shen, X., Zhang, Y., Liang, J., Jiang, S., & Zhang, M. (2025). PolyLink: A Blockchain Based Decentralized Edge AI Platform for LLM Inference. arXiv preprint. https://arxiv.org/abs/2510.02395v1

**Abstract:**

> The rapid advancement of large language models (LLMs) in recent years has revolutionized the AI
> landscape. However, the deployment model and usage of LLM services remain highly centralized,
> creating significant trust issues and costs for end users and developers. To address these issues,
> we propose PolyLink, a blockchain-based decentralized AI platform that decentralizes LLM development
> and inference. Specifically, PolyLink introduces a decentralized crowdsourcing architecture that
> supports single-device and cross-device model deployment and inference across heterogeneous devices
> at the edge. Moreover, to ensure the inference integrity, we design the TIQE protocol, which
> combines a lightweight cross-encoder model and an LLM-as-a-Judge for a high-accuracy inference
> evaluation. Lastly, we integrate a comprehensive token-based incentive model with dynamic pricing
> and reward mechanisms for all participants. We have deployed PolyLink and conducted an extensive
> real-world evaluation through geo-distributed deployment across heterogeneous devices. Results
> indicate that the inference and verification latency is practical. Our security analysis
> demonstrates that the system is resistant to model degradation attacks and validator corruptions.
> PolyLink is now available at https://github.com/IMCL-PolyLink/PolyLink.

### 64. [HadAgent: Harness-Aware Decentralized Agentic AI Serving with Proof-of-Inference Blockchain Consensus](https://arxiv.org/abs/2604.18614)

- **arXiv:** [2604.18614](https://arxiv.org/abs/2604.18614)
- **Date:** published 2026-04-15
- **Authors:** Landy Jimenez, Mariah Weatherspoon, Bingyu Shen, Yi Sheng, Jianming Liu, Boyang Li
- **Categories:** cs.DC, cs.CR, cs.ET, cs.MA
- **Citation:** Jimenez, L., Weatherspoon, M., Shen, B., Sheng, Y., Liu, J., & Li, B. (2026). HadAgent: Harness-Aware Decentralized Agentic AI Serving with Proof-of-Inference Blockchain Consensus. arXiv preprint. https://arxiv.org/abs/2604.18614v1

**Abstract:**

> Proof-of-Work (PoW) blockchain consensus consumes vast computational resources without producing
> useful output, while the rapid growth of large language model (LLM) agents has created unprecedented
> demand for GPU computation. We present HadAgent, a decentralized agentic AI serving system that
> replaces hash-based mining with Proof-of-Inference (PoI), a consensus mechanism in which nodes earn
> block-creation rights by executing deterministic LLM inference tasks. Because verification requires
> only re-executing a single forward pass under identical conditions, cross-node verification operates
> at consensus speed. HadAgent organizes validated records into a three-lane block body with dedicated
> DATA, MODEL, and PROOF channels, each protected by an independent Merkle root for fine-grained
> tamper detection. A two-tier node architecture classifies secondary nodes as trusted or non-trusted
> based on historical behavior: trusted nodes serve inference results in real time through optimistic
> execution, while non-trusted nodes must undergo full consensus verification. A harness layer
> monitors node behavior through heartbeat probes, anomaly detection via deterministic recomputation,
> and automated trust management, creating a self-correcting feedback loop that isolates malicious or
> unreliable participants. Experiments on a prototype implementation demonstrate 100% detection rate
> and 0% false positive rate for tampered records, sub-millisecond validation latency for record and
> hub operations, and effective harness convergence that excludes adversarial nodes within two rounds
> while promoting honest nodes to trusted status within five rounds.

### 65. [Towards Multi-Agent Economies: Enhancing the A2A Protocol with Ledger-Anchored Identities and x402 Micropayments for AI Agents](https://arxiv.org/abs/2507.19550)

- **arXiv:** [2507.19550](https://arxiv.org/abs/2507.19550)
- **Date:** published 2025-07-24
- **Authors:** Awid Vaziry, Sandro Rodriguez Garzon, Axel Küpper
- **Categories:** cs.MA, cs.NI
- **DOI:** 10.1007/978-3-032-15632-7_25
- **Citation:** Vaziry, A., Garzon, S. R., & Küpper, A. (2025). Towards Multi-Agent Economies: Enhancing the A2A Protocol with Ledger-Anchored Identities and x402 Micropayments for AI Agents. arXiv preprint. https://arxiv.org/abs/2507.19550v1

**Abstract:**

> This research article presents a novel architecture to empower multi-agent economies by addressing
> two critical limitations of the emerging Agent2Agent (A2A) communication protocol: decentralized
> agent discoverability and agent-to-agent micropayments. By integrating distributed ledger technology
> (DLT), this architecture enables tamper-proof, on-chain publishing of AgentCards as smart contracts,
> providing secure and verifiable agent identities. The architecture further extends A2A with the x402
> open standard, facilitating blockchain-agnostic, HTTP-based micropayments via the HTTP 402 status
> code. This enables autonomous agents to seamlessly discover, authenticate, and compensate each other
> across organizational boundaries. This work further presents a comprehensive technical
> implementation and evaluation, demonstrating the feasibility of DLT-based agent discovery and
> micropayments. The proposed approach lays the groundwork for secure, scalable, and economically
> viable multi-agent ecosystems, advancing the field of agentic AI toward trusted, autonomous economic
> interactions.

### 66. [Agent Exchange: Shaping the Future of AI Agent Economics](https://arxiv.org/abs/2507.03904)

- **arXiv:** [2507.03904](https://arxiv.org/abs/2507.03904)
- **Date:** published 2025-07-05
- **Authors:** Yingxuan Yang, Ying Wen, Jun Wang, Weinan Zhang
- **Categories:** cs.AI, cs.MA
- **Citation:** Yang, Y., Wen, Y., Wang, J., & Zhang, W. (2025). Agent Exchange: Shaping the Future of AI Agent Economics. arXiv preprint. https://arxiv.org/abs/2507.03904v1

**Abstract:**

> The rise of Large Language Models (LLMs) has transformed AI agents from passive computational tools
> into autonomous economic actors. This shift marks the emergence of the agent-centric economy, in
> which agents take on active economic roles-exchanging value, making strategic decisions, and
> coordinating actions with minimal human oversight. To realize this vision, we propose Agent Exchange
> (AEX), a specialized auction platform designed to support the dynamics of the AI agent marketplace.
> AEX offers an optimized infrastructure for agent coordination and economic participation. Inspired
> by Real-Time Bidding (RTB) systems in online advertising, AEX serves as the central auction engine,
> facilitating interactions among four ecosystem components: the User-Side Platform (USP), which
> translates human goals into agent-executable tasks; the Agent-Side Platform (ASP), responsible for
> capability representation, performance tracking, and optimization; Agent Hubs, which coordinate
> agent teams and participate in AEX-hosted auctions; and the Data Management Platform (DMP), ensuring
> secure knowledge sharing and fair value attribution. We outline the design principles and system
> architecture of AEX, laying the groundwork for agent-based economic infrastructure in future AI
> ecosystems.

### 67. [VeriLLM: A Lightweight Framework for Publicly Verifiable Decentralized Inference](https://arxiv.org/abs/2509.24257)

- **arXiv:** [2509.24257](https://arxiv.org/abs/2509.24257)
- **Date:** published 2025-09-29; updated 2026-01-22
- **Authors:** Ke Wang, Zishuo Zhao, Xinyuan Song, Zelin Li, Libin Xia, Chris Tong, Bill Shi, Wenjie Qu, Eric Yang, Lynn Ai
- **Categories:** cs.CR, cs.LG
- **Citation:** Wang, K., Zhao, Z., Song, X., Li, Z., Xia, L., Tong, C., Shi, B., Qu, W., Yang, E., & Ai, L. (2025). VeriLLM: A Lightweight Framework for Publicly Verifiable Decentralized Inference. arXiv preprint. https://arxiv.org/abs/2509.24257v4

**Abstract:**

> Decentralized inference provides a scalable and resilient paradigm for serving large language models
> (LLMs), enabling fragmented global resource utilization and reducing reliance on centralized
> providers. However, in a permissionless environment without trusted nodes, ensuring the correctness
> of model outputs remains a core challenge. We introduce VeriLLM, a publicly verifiable protocol for
> decentralized LLM inference that achieves security with incentive guarantees while maintaining
> practical efficiency. VeriLLM combines lightweight empirical rerunning with minimal on-chain checks
> to preclude free-riding, allowing verifiers to validate results at approximately 1% of the
> underlying inference cost by exploiting the structural separation between prefill and autoregressive
> decoding. To prevent verification bottlenecks, we design an isomorphic inference--verification
> architecture that multiplexes both inference and verification roles across the same GPU workers.
> This design (i) improves GPU utilization and overall throughput, (ii) enlarges the effective
> validator set, enhancing robustness and liveness, and (iii) enforces task indistinguishability to
> prevent node-specific optimizations or selective behavior. Through theoretical analysis and system-
> level evaluation, we show that VeriLLM achieves reliable public verifiability with minimal overhead,
> offering a practical foundation for trustworthy and scalable decentralized LLM inference.

### 68. [Design and Evaluation of Cost-Aware PoQ for Decentralized LLM Inference](https://arxiv.org/abs/2512.16317)

- **arXiv:** [2512.16317](https://arxiv.org/abs/2512.16317)
- **Date:** published 2025-12-18
- **Authors:** Arther Tian, Alex Ding, Frank Chen, Alan Wu, Aaron Chan, Bruce Zhang
- **Categories:** cs.AI
- **Citation:** Tian, A., Ding, A., Chen, F., Wu, A., Chan, A., & Zhang, B. (2025). Design and Evaluation of Cost-Aware PoQ for Decentralized LLM Inference. arXiv preprint. https://arxiv.org/abs/2512.16317v1

**Abstract:**

> Decentralized large language model (LLM) inference promises transparent and censorship resistant
> access to advanced AI, yet existing verification approaches struggle to scale to modern models.
> Proof of Quality (PoQ) replaces cryptographic verification of computation with consensus over output
> quality, but the original formulation ignores heterogeneous computational costs across inference and
> evaluator nodes. This paper introduces a cost-aware PoQ framework that integrates explicit
> efficiency measurements into the reward mechanism for both types of nodes. The design combines
> ground truth token level F1, lightweight learned evaluators, and GPT based judgments within a
> unified evaluation pipeline, and adopts a linear reward function that balances normalized quality
> and cost. Experiments on extractive question answering and abstractive summarization use five
> instruction tuned LLMs ranging from TinyLlama-1.1B to Llama-3.2-3B and three evaluation models
> spanning cross encoder and bi encoder architectures. Results show that a semantic textual similarity
> bi encoder achieves much higher correlation with both ground truth and GPT scores than cross
> encoders, indicating that evaluator architecture is a critical design choice for PoQ. Quality-cost
> analysis further reveals that the largest models in the pool are also the most efficient in terms of
> quality per unit latency. Monte Carlo simulations over 5\,000 PoQ rounds demonstrate that the cost-
> aware reward scheme consistently assigns higher average rewards to high quality low cost inference
> models and to efficient evaluators, while penalizing slow low quality nodes. These findings suggest
> that cost-aware PoQ provides a practical foundation for economically sustainable decentralized LLM
> inference.

### 69. [Optimistic TEE-Rollups: A Hybrid Architecture for Scalable and Verifiable Generative AI Inference on Blockchain](https://arxiv.org/abs/2512.20176)

- **arXiv:** [2512.20176](https://arxiv.org/abs/2512.20176)
- **Date:** published 2025-12-23
- **Authors:** Aaron Chan, Alex Ding, Frank Chen, Alan Wu, Bruce Zhang, Arther Tian
- **Categories:** cs.CR
- **Citation:** Chan, A., Ding, A., Chen, F., Wu, A., Zhang, B., & Tian, A. (2025). Optimistic TEE-Rollups: A Hybrid Architecture for Scalable and Verifiable Generative AI Inference on Blockchain. arXiv preprint. https://arxiv.org/abs/2512.20176v1

**Abstract:**

> The rapid integration of Large Language Models (LLMs) into decentralized physical infrastructure
> networks (DePIN) is currently bottlenecked by the Verifiability Trilemma, which posits that a
> decentralized inference system cannot simultaneously achieve high computational integrity, low
> latency, and low cost. Existing cryptographic solutions, such as Zero-Knowledge Machine Learning
> (ZKML), suffer from superlinear proving overheads (O(k NlogN)) that render them infeasible for
> billionparameter models. Conversely, optimistic approaches (opML) impose prohibitive dispute
> windows, preventing real-time interactivity, while recent "Proof of Quality" (PoQ) paradigms
> sacrifice cryptographic integrity for subjective semantic evaluation, leaving networks vulnerable to
> model downgrade attacks and reward hacking. In this paper, we introduce Optimistic TEE-Rollups
> (OTR), a hybrid verification protocol that harmonizes these constraints. OTR leverages NVIDIA H100
> Confidential Computing Trusted Execution Environments (TEEs) to provide sub-second Provisional
> Finality, underpinned by an optimistic fraud-proof mechanism and stochastic Zero-Knowledge spot-
> checks to mitigate hardware side-channel risks. We formally define Proof of Efficient Attribution
> (PoEA), a consensus mechanism that cryptographically binds execution traces to hardware
> attestations, thereby guaranteeing model authenticity. Extensive simulations demonstrate that OTR
> achieves 99% of the throughput of centralized baselines with a marginal cost overhead of $0.07 per
> query, maintaining Byzantine fault tolerance against rational adversaries even in the presence of
> transient hardware vulnerabilities.

### 70. [EigenAI: Deterministic Inference, Verifiable Results](https://arxiv.org/abs/2602.00182)

- **arXiv:** [2602.00182](https://arxiv.org/abs/2602.00182)
- **Date:** published 2026-01-30
- **Authors:** David Ribeiro Alves, Vishnu Patankar, Matheus Pereira, Jamie Stephens, Nima Vaziri, Sreeram Kannan
- **Categories:** cs.CR, cs.AI
- **Citation:** Alves, D. R., Patankar, V., Pereira, M., Stephens, J., Vaziri, N., & Kannan, S. (2026). EigenAI: Deterministic Inference, Verifiable Results. arXiv preprint. https://arxiv.org/abs/2602.00182v1

**Abstract:**

> EigenAI is a verifiable AI platform built on top of the EigenLayer restaking ecosystem. At a high
> level, it combines a deterministic large-language model (LLM) inference engine with a
> cryptoeconomically secured optimistic re-execution protocol so that every inference result can be
> publicly audited, reproduced, and, if necessary, economically enforced. An untrusted operator runs
> inference on a fixed GPU architecture, signs and encrypts the request and response, and publishes
> the encrypted log to EigenDA. During a challenge window, any watcher may request re-execution
> through EigenVerify; the result is then deterministically recomputed inside a trusted execution
> environment (TEE) with a threshold-released decryption key, allowing a public challenge with private
> data. Because inference itself is bit-exact, verification reduces to a byte-equality check, and a
> single honest replica suffices to detect fraud. We show how this architecture yields sovereign
> agents -- prediction-market judges, trading bots, and scientific assistants -- that enjoy state-of-
> the-art performance while inheriting security from Ethereum's validator base.

### 71. [FedToken: Tokenized Incentives for Data Contribution in Federated Learning](https://arxiv.org/abs/2209.09775)

- **arXiv:** [2209.09775](https://arxiv.org/abs/2209.09775)
- **Date:** published 2022-09-20; updated 2022-11-03
- **Authors:** Shashi Raj Pandey, Lam Duc Nguyen, Petar Popovski
- **Categories:** cs.LG, cs.DC, cs.GT, cs.NI
- **Citation:** Pandey, S. R., Nguyen, L. D., & Popovski, P. (2022). FedToken: Tokenized Incentives for Data Contribution in Federated Learning. arXiv preprint. https://arxiv.org/abs/2209.09775v2

**Abstract:**

> Incentives that compensate for the involved costs in the decentralized training of a Federated
> Learning (FL) model act as a key stimulus for clients' long-term participation. However, it is
> challenging to convince clients for quality participation in FL due to the absence of: (i) full
> information on the client's data quality and properties; (ii) the value of client's data
> contributions; and (iii) the trusted mechanism for monetary incentive offers. This often leads to
> poor efficiency in training and communication. While several works focus on strategic incentive
> designs and client selection to overcome this problem, there is a major knowledge gap in terms of an
> overall design tailored to the foreseen digital economy, including Web 3.0, while simultaneously
> meeting the learning objectives. To address this gap, we propose a contribution-based tokenized
> incentive scheme, namely \texttt{FedToken}, backed by blockchain technology that ensures fair
> allocation of tokens amongst the clients that corresponds to the valuation of their data during
> model training. Leveraging the engineered Shapley-based scheme, we first approximate the
> contribution of local models during model aggregation, then strategically schedule clients lowering
> the communication rounds for convergence and anchor ways to allocate \emph{affordable} tokens under
> a constrained monetary budget. Extensive simulations demonstrate the efficacy of our proposed
> method.

## Residual search gaps

- This is arXiv-centered. It likely undercovers ACM/USENIX/IEEE papers without arXiv versions, economics/SSRN mechanism-design papers, deployed crypto-project whitepapers, and non-public industrial work.
- Query vocabulary remains a recall risk: related work may use `semivalue`, `Banzhaf value`, `truthful data markets`, `proof of quality`, `proof of inference`, `data dividends`, `secure aggregation contribution`, `data clean room`, `agent provenance`, or `confidential AI` without using the exact framing here.
- Scry broad semantic search was not available for this arXiv surface in the attempted call; the final set is lexical/Scry/arXiv/related-paper grounded rather than semantically exhaustive.

## Query families used

- `confidential computing agentic AI`
- `confidential LLM inference; trusted execution environment large language model inference; secure enclave AI agent; AI agent audit log receipts transparency`
- `privacy-preserving decentralized AI confidential computing; decentralized AI blockchain inference; blockchain AI marketplace agents; verifiable machine learning inference blockchain; zero knowledge machine learning inference`
- `data marketplace Shapley value; Shapley value data valuation machine learning; privacy preserving data valuation marketplace; federated learning contribution Shapley incentive`
- `federated inference privacy-preserving collaborative incentivized model serving; privacy preserving collaborative inference multi party; data clean room privacy preserving machine learning`
- `access control provenance artificial intelligence agent; role based access control data provenance machine learning; accountable AI agents provenance`
