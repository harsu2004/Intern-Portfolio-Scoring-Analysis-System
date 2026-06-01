1. Skill Match Formula:
-->  
   skill_match = (matched_kws / total_skills) * 100

2. Completeness Score Formula:
-->
   completeness = (
      email_score (15) +
      phone_score (15) +
      skill_score (max 30 scaled) +
      education_score (20) +
      project/experience_score (20)
    )

3. ATS Score Formula:
-->
   ats_score = kw_factor + structure_bonus + impact_factor + length_score

where:
     1. Keyword factor =  kw_factor = (matched_keywords / total_skills) * 45
     2. Structure bonus = structure_bonus = number_of_sections_found * 5
     3. Impact factor =  impact_factor = min(15, action_verbs_count * 3)
     
     4. Length score =   if 200 <= word_count <= 600:
                          length_score = 15
                         elif 601 <= word_count <= 950:
                           length_score = 8
                         else:
                           length_score =2

Final ATS clamp: 
                ats_score = max(15, min(ats_score, 100))

                if sections_found < 3:
                   ats_score = min(ats_score, 45)  


4. Resume Quality Score:  quality = 10
--->    
       if skill_match >= 40:
         quality += 30

       if github exists:
         quality += 20

       if strong verbs or achievements exist:
         quality += 20

5. Rule-Based Score Formula:
--->   
       rule_based_score =
          (skill_match * 0.25) +
          (ats_score * 0.27) +
          (quality * 0.21) +
          (completeness * 0.27)  

6. Final Score Formula (IMPORTANT):
-->   
       total_score = (rule_based_score * 0.5) + (ml_score * 0.5)                 

7. ML Model Input (Feature Vector):
-->  
     features = skill_match,quality,completeness,ats_score,matched_keywords,word_count,github flag,department,             github_stars_total,github_repo_count,num_projects,intern_role,internship_batch,tools_used_count

8. Fit Label Logic:
-->
     if total_score >= 70:
      "STRONG FIT"
     elif total_score >= 42:
      "MODERATE MATCH"
     else:
      "NEEDS REFACTOR"

9. Circle Progress UI Formula
-->
    stroke_dashoffset = 377 - (377 * score / 100)

    