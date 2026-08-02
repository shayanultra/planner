# RAGnaroX: A Secure, Local-Hosted ChatOps Assistant Using Small Language Models

Benedikt Dornauer 

University of Innsbruck 

Innsbruck, Austria 

Email: benedikt.dornauer@uibk.ac.at 

ORCID: 0000-0002-7713-4686 

Mircea-Cristian Racasan 

c.c.com Moser GmbH 

Teslastraße 4, 8074 Grambach, Austria 

Email: mracasan@cccom.at 

ORCID: 0009-0008-7938-3126 

Abstract—This paper introduces RAGnaroX, a resource-efficient ChatOps assistant that operates entirely on commodity hardware. Unlike existing solutions that often rely on external providers such as Azure or OpenAI, RAGnaroX offers a fully auditable, on-premise stack implemented in Rust. Its architecture integrates modular data ingestion, hybrid retrieval, and function calling, enabling flexible yet secure deployment. Our evaluation focuses on the RAG pipeline, with benchmarks conducted on the SQuAD (single-hop QA), MultiHopRAG (multi-hop QA), and MLQA (cross-lingual QA) datasets. Results show that RAGnaroX achieves competitive accuracy while maintaining strong resource efficiency, for example, reaching 0.90 context precision on single-hop questions with an average response time of 2.5 seconds per request. A replication package containing the tool, the demonstration video (https://www.youtube.com/watch?v=cDxfuEbcoM4), and all supporting materials are available at https://github.com/genius-itea/RAGnaroX.git. 

Index Terms—Retrieval Augmented Generation, Resource-Efficient, Small Language Models, ChatOps Assistants, Model Context Protocol 

## I. INTRODUCTION

By 2025, more than two-thirds of companies had integrated AI into their business operations across a variety of use cases $[1]$ . Thereby, a commonly seen technique is the enhancement of LLMs through knowledge integration, commonly referred to as Retrieval-Augmented Generation (RAG), which is increasingly combined with function-calling mechanisms. Consequently, as dependence on generative AI grows, so does the risk of vendor lock-in, particularly with major U.S.-based technology firms whose proprietary ecosystems dominate the market $[2]$ . At the same time, China is rapidly expanding its AI capabilities and investments, positioning itself as a significant competitor to U.S. dominance $[3]$ . Overall, the tech industry is investing heavily in frontier LLMs, with compute demand projected to increase 2.25-fold over the next two years $[4]$ . While these advancements are likely to enhance model quality, they are also expected to drive up usage costs. 

The combination of increasing external dependency and escalating costs poses a significant strategic risk to organizations. Additionally, in regulated fields such as medicine and finance, dependence on external AI providers also raises compliance concerns. External (proprietary) hosted models are often difficult to control or audit fully, exposing organizations to legal and reputational risks $[5]$ . 

Given the aforementioned challenges with external, commercial providers, we developed RAGnaroX, an on-premise, auditable RAG stack that combines the advantages of one of the most secure and performant programming languages, Rust [6], and llama.cpp [7] for quantized local inference of large and small language models (SLMs). We further integrated ChatOps, conversational agents embedded in operational workflows to directly execute system actions [8], into RAGnaroX via the Model Context Protocol (MCP) [9], thereby rendering retrieved knowledge operational rather than merely informative. 

## II. CONCEPTION OF RAGNAROX

To reduce integration and operational costs, the hardware requirements for running RAGnaroX were kept to a minimum. Therefore, the target configuration was a commodity computer equipped with 64 GB of RAM and a 24GB VRAM graphics card NVIDIA RTX 4090. However, we expect the requirements to continue declining as the quality of SLMs improves (e.g., RTX 4060). 

The interoperability with existing infrastructures and the adaptability to new requirements, both in software and hardware, were factors that led to the initial decision to adopt a Rust microservice architecture that utilizes HTTP and JSON for interprocess communication. As shown in Figure 1, RAGnaroX's conception is organized around two main components: 

a) Data Integration Component: The modular adaptability enables the integration of various data sources (e.g., GitLab, Redmine) and data types (e.g., emails, files, wiki pages, issues). 

In the first stage of the processing pipeline, the raw artifacts are converted to Markdown (e.g., from Textile), a format chosen because it seems to be highly LM interpretable, providing also simple syntactic markers and a rich toolset to transform to (e.g., PDF → Markdown) [10]. During the conversion phase, redundant repeating sequences (e.g., white spaces and dashes in table headers) are removed, thereby reducing the overall document size. This, in turn, decreases the storage footprint and optimizes the chunking process, enabling faster/efficient loading. 

![image](https://cdn-mineru.openxlab.org.cn/result/2026-08-02/6f475052-1f55-4ba2-9b97-684d1c968795/f7977b9a41918bdd97484a122b0bda9eca7ed2b3cf5fea8481a949ffe63251a0.jpg)



Fig. 1. Conceptual overview of the RAGnaroX data integration and retrieval–generation pipeline for ChatOps.


Each Markdown document is then divided by headings, preserving the document hierarchy. Each heading's contents are separated into paragraphs, tables, lists, and code snippets, an approach already positively supported by findings by Nguyen et al. [11]. The resulting text blocks are paired with their headings and then tokenized to ensure that the text fits the context size of the embedding model (e.g., multilingual-e5-large-instruct). If the text is too large, it is divided by retaining the headings and headers for the tables, ensuring that each part of the information is placed in context, which is crucial for semantic search. Once the chunks are generated, their source and the timestamp of their generation are attached, and their dense and sparse vectors (BM25) are calculated and stored in Parquet data format. 

b) Retrieval and Generation Component: Similar to the backend microservices, the RAGnaroX frontend is built in Rust. This enables the two to exchange data structures and logic. The frontend transmits the chat history to the backend, and the backend uses HTTP to reach all registered RAG source microservices and request all pertinent chunks. Every RAG source uses BM25 and semantic search (cosine similarity) to look for chunks in its embedded database. The hybrid approach to chunk retrieval is predicated on the complementary nature of both algorithms as well as their acknowledged advantages and disadvantages $[12]$ . 

Duplicate entries are eliminated after every RAG source has returned its chunks. Next, a reranker SLM (e.g., bge-rerankerv2-m3) is used to reorder the remaining chunks and eliminate irrelevant information $[12]$ . Due to the finite context size of the reranker, the chunks are grouped by their size in tokens and iteratively reranked in batches until the desired number of chunks remains. 

The next step, which is the foundation of ChatOps, involves using another specialized SLM (e.g., Qwen3-4B-Thinking-2507) to call registered functions via MCP. Due to constraints in the model context size, the prompt is generated iteratively. With each iteration, older chat history messages are removed until all chunks, the description of the available function calls, and the most recent messages in the chat history fit in the context. This procedure adapts to the different model context sizes and also preserves as much pertinent data as possible. Once the model decides which functions to call, the registered MCP endpoints (e.g., GitLab) are invoked, and their responses are added to the RAG chunks. 

The final prompt to generate the user's answer is once again put together in the same manner as for function calling. Once the answer has been streamed token by token, the list of chunks is also transmitted to allow the user to verify the answer. 

## A. Methodology for RAG Evaluation

The evaluation of RAGnaroX centers on the information retrieval task, with three benchmark datasets selected to highlight different challenges commonly encountered in practical deployments: 

![image](https://cdn-mineru.openxlab.org.cn/result/2026-08-02/6f475052-1f55-4ba2-9b97-684d1c968795/308cf3c44a479be0df2d90b95dbfc7472c9ed2e722d118eb5a0891102b1bf450.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-08-02/6f475052-1f55-4ba2-9b97-684d1c968795/1d1440de714379cc35ebc74136c5a61ec03355a257512bf4d201ba9f7b3506e8.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-08-02/6f475052-1f55-4ba2-9b97-684d1c968795/a6df00562788a140d4bf9ca8ede3a450f9f346dbd8af90a940d1f392fec3c98b.jpg)



Fig. 2. Performance Metrics in RAGnaroX, with changed generation models


(i) SQuAD v1.1 [13]: a single-hop factoid QA benchmark requiring answer extraction from a single document, 

(ii) MultiHopRAG [14]: a benchmark for multi-hop reasoning, where answering a query requires integrating evidence across multiple retrieved documents, and 

(iii) MLQA [15]: a cross-lingual QA benchmark for evaluating transfer and retrieval across languages. In these experiments, we focused on English, Spanish, and German. 

To run the RAG experiments, we used an RTX 4090 GPU. If not otherwise mentioned, we employed Qwen3-4B-q8 for generation, multilingual-e5-large-q8 for embedding, and bge-reranker-v2-m3-q8 for reranking, with 350 chunking tokens, and 3 chunks (given as @3). Different components were modified to make them comparable to existing benchmarks [14], [16]. 

We conducted our evaluation with RAGAS [17]. Prior tests with gpt-oss-20B, Qwen3-30B, and gpt-oss-120B showed that results were largely invariant to evaluator size, with deviations $\leq 0.02$ for retrieval metrics (Context Recall@3, Context Precision@3) and $\leq 0.03$ for generation metrics (Faithfulness@3, Answer Relevancy@3) on SQuAD. We selected gpt-oss-20B for its efficiency and to reduce potential bias toward the models under evaluation. 

Apart from that, for each test-run, we logged execution traces using strace for system calls and cProfile for function-level profiling. GPU activity was sampled via nvidia-smi, while CPU and RAM usage were aligned with /proc metrics. 

## III. RESULTS AND DISCUSSION

1) Single-Hop-Dataset (SQuAD v1.1): The results indicate that the retrieval achieved high accuracy, with an average Context Precision@5 of 0.90 and Context Recall@5 of 0.94. In comparison to the Blended-RAG implementation by Sawarkar et al. [16], which also assessed retrieval quality using the top-5 documents, our retrieval component demonstrates performance on par with their different RAG approaches, yielding a comparable level of effectiveness (min.: $90.7\%$ - max.: $94.89\%$ ). 

Using the retrieved chunks, we evaluated five SLMs for answer generation, including Qwen3 models of varying sizes, as well as other recent baselines, as presented in Table I. Notably, the smallest model, Qwen3 (4B), illustrates that increasing model size does not necessarily translate into improved grounding or factual consistency. Indeed, its more limited reliance on parametric knowledge may even constitute an advantage in contexts of knowledge conflict, when retrieved evidence diverges from the model's internal representations, an issue that approaches such as Zhang et al. [18] explicitly aim to address. 


TABLE I



FAITHFULNESS AND ANSWER RELEVANCY COMPARISON


<table><tr><td rowspan="2">Model</td><td colspan="2">Single-hop QA</td><td colspan="2">Multi-hop QA</td></tr><tr><td>Faith.</td><td>AnsRel.</td><td>Faith.</td><td>AnsRel.</td></tr><tr><td>Qwen3 (14B)</td><td>0.8327</td><td>0.7846</td><td>0.7039</td><td>0.6407</td></tr><tr><td>Qwen3 (8B)</td><td>0.8364</td><td>0.7865</td><td>0.6874</td><td>0.6328</td></tr><tr><td>Mistral (7B)</td><td>0.7963</td><td>0.7705</td><td>0.4654</td><td>0.6568</td></tr><tr><td>Gemma-3n-E2B</td><td>0.7183</td><td>0.7722</td><td>0.4067</td><td>0.5056</td></tr><tr><td>Qwen3 (4B)</td><td>0.8588</td><td>0.8168</td><td>0.6341</td><td>0.6790</td></tr><tr><td>Phi-4-mini (4B)</td><td>0.7192</td><td>0.7764</td><td>0.4583</td><td>0.6612</td></tr></table>

2) Multi-Hop-Dataset (MultiHopRAG): In the multi-hop setting, retrieval quality declines, with Context Precision@4 = 0.42 and Context Recall@4 = 0.52. Compared to the benchmark metrics reported by Tang et al. [14], RAGnaroX attains Hits@4 = 0.57, following their evaluation strategy. This places RAGnaroX's retrieval on par with the other multilingual embedding models, such as intfloat/e5-base-v2 and hkunlp/instructor-large, but still behind English embedders, e.g. bge-large-en-v1.5 or text-embedding-ada-002. Thus, further enhancements are needed, such as a knowledge graph-based inclusion, which might further enhance the multi-hop retrieval [19]. Compared to single-hop results, Qwen3 (4B) continues to achieve the highest answer relevancy. In contrast, faithfulness benefits from SLMs with more parameters, likely due to a decrease of the number of retrieved documents and the consequent reliance on the SLM's internal knowledge. 

3) Multi-Language-Dataset (MLQA): Having a look at different language configurations, given in Table II, it is derivable that en-en performs pretty well, as model weights might mainly be trained on the English corpus, specifically for the retrieval part. If we consider non-English languages with the same data corpus and questions (e.g., de-de), the performance drops; if the corpus and language differ, the performance drops even further. It can be seen that here a larger model Qwen3-14B clearly outperforms smaller models Qwen3-4b. 


TABLE II



RAG SYSTEM PERFORMANCE OF QWEN3 14B AND 4B


<table><tr><td rowspan="2">Corpus-Question</td><td rowspan="2">Ctx. P.</td><td rowspan="2">Ctx. R.</td><td colspan="2">Faith.</td><td colspan="2">AnsRel.</td></tr><tr><td>14B</td><td>4B</td><td>14B</td><td>4B</td></tr><tr><td>en-en</td><td>0.86</td><td>0.91</td><td>0.83</td><td>0.81</td><td>0.73</td><td>0.75</td></tr><tr><td>de-de</td><td>0.74</td><td>0.77</td><td>0.77</td><td>0.73</td><td>0.41</td><td>0.44</td></tr><tr><td>es-es</td><td>0.82</td><td>0.87</td><td>0.77</td><td>0.80</td><td>0.53</td><td>0.58</td></tr><tr><td>en-de</td><td>0.59</td><td>0.70</td><td>0.74</td><td>0.70</td><td>0.41</td><td>0.43</td></tr><tr><td>de-en</td><td>0.64</td><td>0.73</td><td>0.73</td><td>0.71</td><td>0.71</td><td>0.65</td></tr><tr><td>en-es</td><td>0.64</td><td>0.71</td><td>0.74</td><td>0.73</td><td>0.54</td><td>0.52</td></tr><tr><td>de-es</td><td>0.50</td><td>0.63</td><td>0.71</td><td>0.61</td><td>0.52</td><td>0.47</td></tr><tr><td>es-en</td><td>0.71</td><td>0.81</td><td>0.75</td><td>0.73</td><td>0.69</td><td>0.69</td></tr><tr><td>es-de</td><td>0.52</td><td>0.72</td><td>0.70</td><td>0.65</td><td>0.45</td><td>0.44</td></tr></table>

4) Energy-Drawn: Since the SLMs are executed locally, see Figure 2, energy consumption must also be considered. In this regard, Phi-4-mini performs best. Interestingly, Qwen exhibits significantly higher energy consumption in multi-hop scenarios, which may be attributed to longer reasoning times. 

5) Response Latency: An essential aspect of a ChatOps assistant is its performance, particularly its responsiveness. The results, illustrated in Figure 2, indicate that pipelines employing generative models with fewer than 5B parameters achieve response times below 2.5 s for single-hop queries and 3.8 s for multi-hop queries. Such delays are considered satisfactory from a user perspective, based on the findings by Maslych et al [20]. 

## Comparing RAGnaroX in Real-World QA

Beyond the benchmark results, we further evaluated our approach on a documentation-based use case from CAS-BLANCA hotelsoftware, employing 250 factoid QA pairs. In this setting, CASBLANCA's production-ready RAG system, built with an agentic approach leveraging Azure components and the latest commercial models, achieved $7\%$ higher Context Recall@10 (RAGnaroX: 0.83, CASABLANCA RAG: 0.90), while maintaining nearly the same answer relevancy against RAGnaroX. For generation metrics, RAGnaroX exhibited $12\%$ lower Faithfulness@10 when CASBLANCA 's RAG used GPT-4.1 for generation, but comparable results when they used GPT-4.1-mini. This comparison suggests RAGnaroX is capable of handling real-world data. Nevertheless, further evaluation and empirical evidence are required to compare its effectiveness in real-world settings (performance, costs, usability, etc.). 

## IV. CONCLUSION AND FUTURE OUTLOOK

RAGnaroX is a resource-efficient architecture that can serve as the foundation for various use cases, featuring a function-calling mechanism and secure on-site operability. A concrete example can be seen in the demonstration video, where a ticket support system is simulated: A customer support representative can access the documentation information of CASBLANCA hotelsoftware, and create new issues via chat. Overall, focusing on the information retrieval part, the resource-efficient conception performs reliably for single-faceted questions within acceptable response times. Based on the findings, we will focus on two directions: (1) extending support for multi-hop questions through knowledge-graph integration, and (2) trying to improve cross-language performance through pre-translation. Furthermore, future work will include benchmarks for function calling. 

## REFERENCES



[1] S. Rosenbush, “Why Companies Are Already All-In on AI After Arriving Late to Everything Else,” Wall Street Journal, Jun. 2025. 





[2] E. Howcroft, “Banks say growing reliance on Big Tech for AI carries new risks,” Reuters, Jun. 2024. 





[3] B. AlShebli, S. A. Memon, J. A. Evans, and T. Rahwan, “China and the U.S. produce more impactful AI research when collaborating together,” Scientific Reports, vol. 14, no. 1, p. 28576, Nov. 2024. 





[4] I. Kumar and S. Manning, “Trends in Frontier AI Model Count: A Forecast to 2028,” 2025. 





[5] T. Szadeczky and Z. Bederna, “Risk, regulation, and governance: Evaluating artificial intelligence across diverse application scenarios,” Security Journal, vol. 38, no. 1, p. 35, Mar. 2025. 





[6] W. Bugden and A. Alahmar, “Rust: The Programming Language for Safety and Performance,” Jun. 2022. 





[7] G. Gerganov, "LLM inference in C/C++," ggml, Sep. 2025. 





[8] F. Peci, E. Hamiti, and I. Khan, “Agentic AI with Chatops for Large Scale Network Operations,” in 2025 IEEE Conference on Artificial Intelligence (CAI). Santa Clara, CA, USA: IEEE, May 2025, pp. 1617–1626. 





[9] N. Krishnan, “Advancing Multi-Agent Systems Through Model Context Protocol: Architecture, Implementation, and Applications,” Apr. 2025. 





[10] Z. Chen, Y. Liu, L. Shi, Z.-J. Wang, X. Chen, Y. Zhao, and F. Ren, "MDEval: Evaluating and Enhancing Markdown Awareness in Large Language Models," in Proceedings of the ACM on Web Conference 2025. Sydney NSW Australia: ACM, Apr. 2025, pp. 2981–2991. 





[11] H.-T. Nguyen, T.-D. Nguyen, and V.-H. Nguyen, “Enhancing Retrieval Augmented Generation with Hierarchical Text Segmentation Chunking,” in Information and Communication Technology, W. Buntine, M. Fjeld, T. Tran, M.-T. Tran, B. Huynh Thi Thanh, and T. Miyoshi, Eds. Singapore: Springer Nature Singapore, 2025, vol. 2352, pp. 209–220. 





[12] A. Rao, H. Alipour, and N. Pendar, “Rethinking Hybrid Retrieval: When Small Embeddings and LLM Re-ranking Beat Bigger Models,” May 2025. 





[13] P. Rajpurkar, J. Zhang, K. Lopyrev, and P. Liang, “SQuAD: 100,000+ Questions for Machine Comprehension of Text,” Oct. 2016. 





[14] Y. Tang and Y. Yang, “MultiHop-RAG: Benchmarking Retrieval-Augmented Generation for Multi-Hop Queries,” Jan. 2024. 





[15] P. Lewis, B. Oguz, R. Rinott, S. Riedel, and H. Schwenk, “MLQA: Evaluating Cross-lingual Extractive Question Answering,” in Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics. Online: Association for Computational Linguistics, 2020, pp. 7315–7330. 





[16] K. Sawarkar, A. Mangal, and S. R. Solanki, “Blended RAG: Improving RAG (Retriever-Augmented Generation) Accuracy with Semantic Search and Hybrid Query-Based Retrievers,” in 2024 IEEE 7th International Conference on Multimedia Information Processing and Retrieval (MIPR). San Jose, CA, USA: IEEE, Aug. 2024, pp. 155–161. 





[17] S. Es, J. James, L. Espinosa Anke, and S. Schockaert, “RAGAs: Automated Evaluation of Retrieval Augmented Generation,” in Proceedings of the 18th Conference of the European Chapter of the Association for Computational Linguistics: System Demonstrations. St. Julians, Malta: Association for Computational Linguistics, 2024, pp. 150–158. 





[18] Q. Zhang, Z. Xiang, Y. Xiao, L. Wang, J. Li, X. Wang, and J. Su, “FaithfulRAG: Fact-Level Conflict Modeling for Context-Faithful Retrieval-Augmented Generation,” 2025. 





[19] H. Han, H. Shomer, Y. Wang, Y. Lei, K. Guo, Z. Hua, B. Long, H. Liu, and J. Tang, “RAG vs. GraphRAG: A Systematic Evaluation and Key Insights,” Feb. 2025. 





[20] M. Maslych, M. Katebi, C. Lee, Y. Hmaiti, A. Ghasemaghaei, C. Pumarada, J. Palmer, E. S. Martinez, M. Emporio, W. Snipes, R. P. McMahan, and J. J. L. Jr, “Mitigating Response Delays in Free-Form Conversations with LLM-powered Intelligent Virtual Agents,” 



in Proceedings of the 7th ACM Conference on Conversational User Interfaces, Jul. 2025, pp. 1–15. 
