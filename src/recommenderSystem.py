import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import os

def load_dataset():
    """
    Load the dataset consisting of ratings and movies.

    Returns:
        DataFrame: Merged DataFrame containing ratings and movies information.
    """
    ratings = pd.read_csv('ml-latest-small/ratings.csv',usecols=range(3))
    movies = pd.read_csv('ml-latest-small/movies.csv',usecols=range(2))
    ratings = pd.merge(ratings, movies)
    return ratings

def load_correlation_matrix():
    """
    Load the pre-computed correlation matrix from file.

    Returns:
        DataFrame: Loaded correlation matrix.
    """
    correlation_matrix = pd.read_csv('src/pearsonCorrelationMatrix.csv')

    return correlation_matrix

def does_correlation_matrix_exist():
    """
    Check if the correlationMatrix.csv file exists.

    Returns:
        bool: True if the file exists, False otherwise.
    """
    filename = 'src/correlationMatrix.csv'
   
    return os.path.exists(filename)

def pearson_similarity_matrix(ratings):
    """
    Compute the Pearson correlation matrix between users based on their ratings.

    Parameters:
        ratings (DataFrame): DataFrame containing user ratings with columns: 'userId', 'movieId', 'rating'.

    Returns:
        DataFrame: Pearson correlation matrix between users.
    """
    user_movie_matrix = ratings.pivot_table(index='userId', columns='movieId', values='rating').fillna(0)
    correlation_matrix = np.corrcoef(user_movie_matrix)

    np.fill_diagonal(correlation_matrix, 0)  # Setting self-similarity to 0

    correlation_df = pd.DataFrame(correlation_matrix, index=user_movie_matrix.index, columns=user_movie_matrix.index)
    correlation_df.to_csv('pearsonCorrelationMatrix.csv', index=False)

    return correlation_df

def cosine_similarity_matrix(ratings):
    """
    Compute the cosine similarity matrix between users based on their ratings.

    Parameters:
        ratings (DataFrame): DataFrame containing user ratings with columns: 'userId', 'movieId', 'rating'.

    Returns:
        DataFrame: Cosine similarity matrix between users.
    """
    user_movie_matrix = ratings.pivot_table(index='userId', columns='movieId', values='rating').fillna(0)
   
    similarity_matrix = cosine_similarity(user_movie_matrix)
    np.fill_diagonal(similarity_matrix, 0)  # Setting self-similarity to 0
    similarity_df = pd.DataFrame(similarity_matrix, index=user_movie_matrix.index, columns=user_movie_matrix.index)
    
    return similarity_df

def get_top_similar_users(similarity_df, target_user, n=40):
    """
    Retrieve the top similar users for a target user based on a similarity matrix.

    Parameters:
        similarity_df (DataFrame): DataFrame containing the similarity matrix between users.
        target_user (int): The ID of the target user.
        n (int): Number of top similar users to retrieve. Default is 40.

    Returns:
        Series: Series containing the top similar users for the target user.
    """
    similar_users = similarity_df[target_user].sort_values(ascending=False)[0:n]
    top_similar_users = similar_users.head(10)
    print("\nTop 10 most similar users for target user with ID",target_user)
    for user_index, similarity_score in top_similar_users.items():
        print("user",user_index, ":", round(similarity_score,2))

    return similar_users

def get_user_ratings(ratings, user):
    """
    Retrieve ratings of a specific user from the ratings DataFrame.

    Parameters:
        ratings (DataFrame): DataFrame containing user ratings with columns: 'userId', 'movieId', 'rating'.
        user (int): The ID of the user.

    Returns:
        DataFrame: DataFrame containing ratings of the specified user.
    """
    return ratings[ratings['userId'] == user]

def predict_ratings(ratings, similarity_df, target_user):
    """
    Predicts movie ratings for a target user based on collaborative filtering.

    Parameters:
    - ratings (DataFrame): DataFrame containing user ratings with columns: 'userId', 'movieId', 'rating'.
    - similarity_df (DataFrame): DataFrame containing the similarity matrix between users.
    - target_user (int): The ID of the target user.

    Returns:
    - predicted_ratings (dict): Dictionary containing predicted ratings for movies.
     """
    target_user_ratings = ratings[ratings['userId'] == target_user]
    target_user_mean_rating = target_user_ratings['rating'].mean()
    
    predicted_ratings = {}
    similar_users_mean_rating = {}
    user_ratings_dict = {}
    
    similar_users = get_top_similar_users(similarity_df, target_user)
    
    similar_users_seen_movies = ratings[ratings['userId'].isin(similar_users.index)]
    
    unseen_movies = similar_users_seen_movies[~similar_users_seen_movies['movieId'].isin(target_user_ratings['movieId'])][['movieId', 'title']].drop_duplicates() 
    
    # Pre-calculate the mean rating of similar users
    for user, similarity in similar_users.items():
        user_ratings = ratings[ratings['userId'] == user]
        similar_users_mean_rating[user] = user_ratings['rating'].mean()
        user_ratings_dict[user] = dict(zip(user_ratings['movieId'], user_ratings['rating']))

    for _, row in unseen_movies.iterrows():
        movie_id = row['movieId']
        movie_title = row['title']

        weighted_sum = 0
        similarity_sum = 0
        
        for user, similarity in similar_users.items():
            if movie_id in user_ratings_dict[user]:
                user_rating = user_ratings_dict[user][movie_id]
                weighted_sum += similarity * (user_rating - similar_users_mean_rating[user])
                similarity_sum += similarity
                
        if similarity_sum != 0:
            predicted_rating = target_user_mean_rating + (weighted_sum / similarity_sum)
            predicted_ratings[movie_title] = predicted_rating    

    return predicted_ratings

def recommend_movies(predictions, n=10):
    """
    Recommends top movies for a user based on predicted ratings.

    Parameters:
    - predictions (dict): Dictionary containing predicted ratings for movies.
    - n (int): Number of top movies to recommend. Default is 10.

    Returns:
    - top_movies (list): List of tuples containing top recommended movies and their predicted ratings.
    """
    top_movies = sorted(predictions.items(), key=lambda x: x[1], reverse=True)[:n]
    return top_movies