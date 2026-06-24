"""
Skill taxonomy for the Redrob Senior AI Engineer JD.

Built by manually reviewing the full 133-skill vocabulary present in the dataset
(see notebooks/explore2.py output) against what the JD says it needs.

Categories:
- CORE_MUST_HAVE: directly named as "absolutely need" in the JD
  (embeddings, vector DB/hybrid search, evaluation-for-ranking, Python)
- ADJACENT_NICE_TO_HAVE: JD says "like to have, won't reject without"
  (LLM fine-tuning, learning-to-rank models, distributed systems, OSS)
- GENERAL_ML_ENGINEERING: broader applied-ML/data-engineering skills that support
  but don't directly demonstrate the JD's specific ask
- DISQUALIFYING_ADJACENT: JD explicitly says these alone are NOT a fit
  (computer vision / speech / robotics without NLP+IR exposure)
- IRRELEVANT: skills with no bearing on this JD (sales, accounting, design, etc.)
  Used as a negative signal only if they dominate a candidate's skill list.
"""

CORE_MUST_HAVE = {
    # embeddings-based retrieval (JD: "sentence-transformers, OpenAI embeddings, BGE, E5, or similar")
    "Embeddings", "Sentence Transformers", "Vector Representations", "Text Encoders",
    "Semantic Search", "Vector Search",
    # vector DB / hybrid search infra (JD: "Pinecone, Weaviate, Qdrant, Milvus, OpenSearch,
    # Elasticsearch, FAISS, or similar")
    "Pinecone", "Weaviate", "Qdrant", "Milvus", "OpenSearch", "Elasticsearch", "FAISS",
    "pgvector", "BM25", "Search Infrastructure", "Search Backend", "Indexing Algorithms",
    "Information Retrieval", "Information Retrieval Systems",
    # ranking + evaluation (JD: "NDCG, MRR, MAP, offline-to-online correlation, A/B testing")
    "Ranking Systems", "Learning to Rank", "Recommendation Systems", "Search & Discovery",
    # core language
    "Python",
}

ADJACENT_NICE_TO_HAVE = {
    # LLM fine-tuning (LoRA, QLoRA, PEFT)
    "LoRA", "QLoRA", "PEFT", "Fine-tuning LLMs", "Model Adaptation",
    "Hugging Face Transformers", "LLMs", "RAG", "Prompt Engineering",
    "LangChain", "LlamaIndex", "Haystack",
    # distributed systems / scale
    "Kubeflow", "MLOps", "MLflow", "Weights & Biases", "Kubernetes", "Docker",
    "Kafka", "Spark", "Databricks", "Apache Beam", "Apache Flink",
    # general ML/DL foundation (supports "understood retrieval before it was fashionable")
    "Machine Learning", "Deep Learning", "Data Science", "Feature Engineering",
    "Statistical Modeling", "PyTorch", "TensorFlow", "scikit-learn",
    "Natural Language Processing", "NLP", "Reinforcement Learning", "BentoML",
}

# JD: "People whose primary expertise is computer vision, speech, or robotics without
# significant NLP/IR exposure" -> explicitly NOT a fit on their own.
DISQUALIFYING_ADJACENT_CV_SPEECH = {
    "Computer Vision", "Image Classification", "Object Detection", "OpenCV", "YOLO",
    "CNN", "GANs", "Diffusion Models",
    "Speech Recognition", "ASR", "TTS",
}

GENERAL_ENGINEERING = {
    "SQL", "PostgreSQL", "MongoDB", "Redis", "BigQuery", "Snowflake", "dbt",
    "Airflow", "ETL", "Data Pipelines", "Workflow Orchestration",
    "REST APIs", "GraphQL", "gRPC", "FastAPI", "Flask", "Django", "Spring Boot",
    "Microservices", "CI/CD", "Terraform", "AWS", "GCP", "Azure",
    "Java", "Go", "Rust", "TypeScript", "JavaScript", "Node.js", "Hadoop",
    "Time Series", "Forecasting", "Document Processing", "Content Matching",
    "Open-source ML libraries",
}

IRRELEVANT = {
    "HTML", "CSS", "React", "Vue.js", "Angular", "Redux", "Next.js", "Webpack", "Tailwind",
    "Figma", "Illustrator", "Photoshop", "Content Writing", "SEO", "Marketing", "Sales",
    "Salesforce CRM", "Accounting", "Tally", "Excel", "PowerPoint", "SAP", "Six Sigma",
    "Agile", "Scrum", "Project Management",
}

ALL_KNOWN = (CORE_MUST_HAVE | ADJACENT_NICE_TO_HAVE | DISQUALIFYING_ADJACENT_CV_SPEECH
             | GENERAL_ENGINEERING | IRRELEVANT)


def skill_category(name: str) -> str:
    if name in CORE_MUST_HAVE:
        return "core"
    if name in ADJACENT_NICE_TO_HAVE:
        return "adjacent"
    if name in DISQUALIFYING_ADJACENT_CV_SPEECH:
        return "cv_speech"
    if name in GENERAL_ENGINEERING:
        return "general_eng"
    if name in IRRELEVANT:
        return "irrelevant"
    return "unknown"
