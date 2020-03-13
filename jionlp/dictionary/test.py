# -*- coding -*-


from bbd_nlp_apis.gadget.file_io import read_file_by_line, write_file_by_line


seqing1 = read_file_by_line('politics.txt')
seqing2 = read_file_by_line('zhengzhi.txt')

seqing = sorted(list(set(seqing1 + seqing2)))

write_file_by_line(seqing, 'zhengzhi_all')
