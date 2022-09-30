#!/bin/bash

# make sure your python path is like the below ones.
# python: /home/ubuntu/anaconda3/bin/python
# working in the directory with `setup.py` file.

# get the latest jionlp version
current_dir_path=$(pwd)
echo "Current directory: $current_dir_path"

jionlp_version=`cat ${current_dir_path}/jionlp/__init__.py | grep -iPo "(?<=(__version__ = \'))([0-9]{1,2}.[0-9]{1,2}.[0-9]{1,2})"`
echo "jionlp version: ${jionlp_version}"


# clean redundant dirs
if [ -d build ]; then
    rm -rf build
fi
if [ -d jionlp.egg-info ]; then
    rm -rf jionlp.egg-info
fi

to_be_deleted=(
  char_distribution.json
  china_location.txt
  chinese_char_dictionary.txt
  chinese_idiom.txt
  chinese_word_dictionary.txt
  idf.txt
  phone_location.txt
  pinyin_phrase.txt
  pornography.txt
  sentiment_words.txt
  topic_word_weight.json
  word_distribution.json
  word_topic_weight.json
  xiehouyu.txt)
for item in ${to_be_deleted[*]};
do
    if [ -f ./jionlp/dictionary/$item ]; then
        echo "deleting redundant file: " $item
        rm -rf ./jionlp/dictionary/$item
fi
done

# char_distribution.json
python3 setup.py bdist_wheel --universal

ls -lth ./dist/ | grep ${jionlp_version}
pip install twine
twine upload ./dist/jionlp-${jionlp_version}-py2.py3-none-any.whl

echo "finished!"
exit 0
