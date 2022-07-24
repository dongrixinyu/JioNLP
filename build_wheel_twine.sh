#!/bin/bash

# make sure your python path is like the below ones.
# python: /home/ubuntu/anaconda3/bin/python
# working in the directory with `setup.py` file.

jionlp_version="1.4.7"

if [ -d build ]; then
    rm -rf build
fi
if [ -d jiojio.egg-info ]; then
    rm -rf jiojio.egg-info
fi

to_be_deleted = (
  "char_distribution.json",
  "china_location.txt",
  "chinese_char_dictionary.txt",
  "chinese_idiom.txt",
  "chinese_word_dictionary.txt",
  "idf.txt",
  "phone_location.txt",
  "pinyin_phrase.txt",
  "pornography.txt",
  "sentiment_words.txt",
  "topic_word_weight.json",
  "word_distribution.json",
  "word_topic_weight.json",
  "xiehouyu.txt"
  )
for item in "${to_be_deleted[@]}";
do
    if [ -d ./jionlp/dictionary/${item} ]; then
        echo "$item"
        rm -rf ./jionlp/dictionary/${item}
fi
done

# char_distribution.json
python3 setup.py bdist_wheel --universal

pip install twine
twine upload dist/jionlp-${jiojio_version}*whl

echo "finished!"
exit 0
