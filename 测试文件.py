#导入execl到 test.db 
import pandas as pd
#文件地址"C:\Users\查志伟\Downloads\车辆信息_委办.xls"
file_path = r'C:\Users\查志伟\Downloads\车辆信息_委办.xls'
# 读取Excel文件
df = pd.read_excel('test.xlsx')
print(df)

