from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def calculate_match_score(resume_text: str, job_description: str) -> dict:
    """
    Calculates the similarity score between a resume and a job description
    using TF-IDF vectors and Cosine Similarity.
    """
    try:
        # Preprocessing: Basic list of 2 documents
        documents = [resume_text, job_description]
        
        # Create TF-IDF Vectors
        tfidf_vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = tfidf_vectorizer.fit_transform(documents)
        
        # Calculate Cosine Similarity (0 to 1)
        # matrix[0] is resume, matrix[1] is job
        score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        
        # Convert to percentage
        match_percentage = round(score * 100, 2)
        
        # Identify Keyword Gaps (Basic)
        feature_names = tfidf_vectorizer.get_feature_names_out()
        resume_vector = tfidf_matrix[0].toarray()[0]
        job_vector = tfidf_matrix[1].toarray()[0]
        
        missing_keywords = []
        for i, word in enumerate(feature_names):
            # If word is in job but score in resume is 0 (or very low)
            if job_vector[i] > 0 and resume_vector[i] == 0:
                missing_keywords.append(word)
                
        # Limit missing keywords to top relevant ones (heuristic)
        missing_keywords = missing_keywords[:10] 

        return {
            "match_percentage": match_percentage,
            "missing_keywords": missing_keywords
        }
    
    except Exception as e:
        print(f"Matching Error: {e}")
        return {"match_percentage": 0, "missing_keywords": [], "error": str(e)}
