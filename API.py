from fastapi import FastAPI, Query
from pydantic import BaseModel
from dictionary_based_scorer_weighted import score_songs


app = FastAPI()


class Response(BaseModel):
    output_path: str
    message: str


@app.get("/lyrics-analyze")
def get_lyrics_analysis_result(keywords_path):
    try:
        result = score_songs(keywords_path)
        message = "success"
    except:
        result = ""
        message = "error"
    finally:
        response = Response(output_path=result, message=message)
    return response


"""    http://127.0.0.1:8000/lyrics-analyze?departure_date=27/5/2021&headcount=4&age=25&age=10&age=34&age=32&city=dhaka&arrival_date=29/5/2021    """
"""    http://127.0.0.1:8000/set-fare?baseprice=100&discount=10 """
