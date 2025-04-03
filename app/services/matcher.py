from sentence_transformers import SentenceTransformer, util
import torch

# Load the model - this would typically be done once and reused
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

def match_roles(parsed_resume: dict, job_descriptions: list) -> list:
    """Match resume against job descriptions using semantic similarity"""
    
    # Convert resume to a single string for comparison
    resume_text = f"{parsed_resume.get('summary', '')} {parsed_resume.get('experience', '')} {parsed_resume.get('education', '')} {' '.join(parsed_resume.get('skills', []))}"
    
    # Encode resume and job descriptions
    resume_embedding = model.encode(resume_text, convert_to_tensor=True)
    job_embeddings = model.encode(job_descriptions, convert_to_tensor=True)
    
    # Calculate cosine similarity
    cosine_scores = util.cos_sim(resume_embedding, job_embeddings)
    
    # Create result list with job match scores
    results = []
    for i, job_desc in enumerate(job_descriptions):
        score = cosine_scores[0][i].item()  # Convert tensor to float
        results.append({
            "job_description": job_desc[:100] + "...",  # Truncate for brevity
            "match_score": round(score * 100, 2),  # Convert to percentage
            "match_strength": get_match_strength(score)
        })
    
    # Sort by score descending
    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results

def get_match_strength(score: float) -> str:
    """Convert numerical score to descriptive strength"""
    if score >= 0.8:
        return "Excellent match"
    elif score >= 0.7:
        return "Strong match"
    elif score >= 0.6:
        return "Good match"
    elif score >= 0.5:
        return "Moderate match"
    else:
        return "Weak match"