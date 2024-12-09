import jionlp as jio
import time
from jionlp.algorithm.ner.time_extractor import TimeExtractor

time_extractor = TimeExtractor()
query = "双十一期间"

res = time_extractor(query, time_base=time.time())
print(res)