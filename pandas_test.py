import pandas as pd


class SLG:
    def __init__(self, excel_path):  # 类的init方法中放入读取的excel路径
        self.df = pd.DataFrame(pd.read_excel(excel_path))
        self.data = self.df[['DATATIME']]
        self.all_status = self.df[['GENE1_RS 1#内燃机状态', 'GENE2_RS 2#内燃机状态', 'LBAR1_RS 1#溴机运行状态', 'LBAR2_RS 2#溴机运行状态',
                                   'CH1_RS #1电制冷状态', 'CH2_RS #2电制冷状态', 'CH3_RS #3电制冷状态',
                                   'CH4_RS #4电制冷状态', 'CH5_RS #5电制冷状态', 'CH6_RS #6电制冷状态']]
        self.cooling = 0             # 制冷机总制冷量

    # 抓取到所有机组的启停状态（溴机-电制冷机）
    def start_status(self):
        all_status = pd.concat([self.data, self.all_status], axis=1)
        return all_status

    # 吸收式制冷机每五分钟制冷总量，单位是KWh
    def ab_c(self):
        ab_c_1 = self.df[['FT411', 'TT412', 'TT411']]  # 分别对应的是冷冻水流量、回水温度、供水温度
        ab_c_2 = self.df[['FT412', 'TT414', 'TT413']]  # 分别对应的是冷冻水流量、回水温度、供水温度
        # dataframe中取某一列值的操作稍许有些不同-->  self.all_status[self.all_status.columns[2]]
        ab_c_1 = self.all_status[self.all_status.columns[2]] * (7 / 6) * ab_c_1[ab_c_1.columns[0]] * (
                ab_c_1[ab_c_1.columns[1]] - ab_c_1[ab_c_1.columns[2]]) * (5 * 60 / 3600)  # 制冷量 = 启停系数*流量*供回水温度差*某一常数
        ab_c_2 = self.all_status[self.all_status.columns[3]] * (7 / 6) * ab_c_2[ab_c_2.columns[0]] * (
                ab_c_2[ab_c_2.columns[1]] - ab_c_2[ab_c_2.columns[2]]) * (5 * 60 / 3600)  # 制冷量 = 启停系数*流量*供回水温度差
        ab_c_total = pd.concat([self.data, ab_c_1, ab_c_2], axis=1)
        ab_c_total.columns = ['DATATIME', '每五分钟1#溴机制冷总量', '2#溴机制冷量(KWh)']
        self.cooling += (ab_c_2 + ab_c_1)
        return ab_c_total

    # 电制冷机每五分钟制冷总量，单位是KWh
    def ec_c(self):
        ec_ = self.df[['FT413', 'TT416', 'TT415',  # 对应1-6号制冷机组
                       'FT414', 'TT418', 'TT417',  # 对应冷冻水流量、回水温度、供水温度
                       'FT415', 'TT420', 'TT419',
                       'FT416', 'TT422', 'TT421',
                       'FT417', 'TT424', 'TT423',
                       'TT426', 'TT425']]  # 6号机组确实冷冻水流量，需要额外进行编程计算
        # 6号的流量 = 冷冻二次管流量 + 冷旁管道流量 - 各机组启停系数*流量
        ec_6 = (self.df['FT461'] + self.df['FT453'] - self.df['FT412'] * self.all_status[self.all_status.columns[3]] -
                self.df['FT411'] * self.all_status[self.all_status.columns[2]] -
                self.df['FT413'] * self.all_status[self.all_status.columns[4]] -
                self.df['FT414'] * self.all_status[self.all_status.columns[5]] -
                self.df['FT415'] * self.all_status[self.all_status.columns[6]] -
                self.df['FT416'] * self.all_status[self.all_status.columns[7]] -
                self.df['FT417'] * self.all_status[self.all_status.columns[8]])
        ec_1 = self.df['FT413'] * self.all_status[self.all_status.columns[4]] * (
                ec_[ec_.columns[1]] - ec_[ec_.columns[2]]) * (7 / 6) * (5 * 60 / 3600)
        ec_2 = self.df['FT414'] * self.all_status[self.all_status.columns[5]] * (
                ec_[ec_.columns[4]] - ec_[ec_.columns[5]]) * (7 / 6) * (5 * 60 / 3600)
        ec_3 = self.df['FT415'] * self.all_status[self.all_status.columns[6]] * (
                ec_[ec_.columns[7]] - ec_[ec_.columns[8]]) * (7 / 6) * (5 * 60 / 3600)
        ec_4 = self.df['FT416'] * self.all_status[self.all_status.columns[7]] * (
                ec_[ec_.columns[10]] - ec_[ec_.columns[11]]) * (7 / 6) * (5 * 60 / 3600)
        ec_5 = self.df['FT417'] * self.all_status[self.all_status.columns[8]] * (
                ec_[ec_.columns[13]] - ec_[ec_.columns[14]]) * (7 / 6) * (5 * 60 / 3600)
        ec_6 = ec_6 * self.all_status[self.all_status.columns[9]] * (
                ec_[ec_.columns[15]] - ec_[ec_.columns[16]]) * (7 / 6) * (5 * 60 / 3600)
        ec_total = pd.concat([self.data, ec_1, ec_2, ec_3, ec_4, ec_5, ec_6], axis=1)
        ec_total.columns = ['DATATIME', '每五分钟1号制冷量', '2号制冷量(KWh)', '3号制冷量', '4号制冷量', '5号制冷量', '6号制冷量']
        self.cooling += (ec_6 + ec_5 + ec_4 + ec_3 + ec_2 + ec_1)
        return ec_total

    # 所有制冷机组每五分钟制冷总量，单位是KWh
    def total_cooling(self):
        SLG.ec_c(self)     # 调用类中电制冷方法
        SLG.ab_c(self)     # 调用类中溴机制冷方法
        total_cooling = pd.concat([self.data, self.cooling], axis=1)
        total_cooling.columns = ["DATATIME", '每5分钟中制冷总量(KWh)']
        return total_cooling

    # 计算每五分钟蓄能罐释冷总量，单位是KWh[正值为释冷，负值为蓄冷]  冷负荷-制冷量
    def storage_cooling(self):
        storage = ((self.df['FT461'] * (self.df['TT462'] - self.df['TT461']) * (7/6) * (5 * 60 / 3600)) -
                   self.cooling)
        total_storage = pd.concat([self.data, storage], axis=1)
        total_storage.columns = ['DATATIME', '每五分钟蓄能罐释冷总量']
        return total_storage

    # 计算每5分钟天然气消耗量，单位是m³
    def gas_total(self):
        ice_1 = self.df[['1#GNGJZHLJ 1#内燃机燃气表校正后累计数值']]# 单位是立方米
        ice_2 = self.df[['2#GNGJZHLJ 2#内燃机燃气表校正后累计数值']]    #累计值的当前行 - 上一行为每五分钟消耗量
        ice_gas_total = pd.concat([self.data, ice_1.diff(), ice_2.diff()], axis=1).loc[1:]
        ice_gas_total.columns = ['DATATIME', '1号天然气消耗量', '2号天然气消耗量']
        return ice_gas_total

    # 计算每五分钟中的总买电量,单位是KWh
    def buy_total(self):
        buy_1 = self.df[['#1隔离变系统侧开关有功']]
        buy_2 = self.df[['#2隔离变系统侧开关有功']]
        for i in range(len(self.data)):  #有功大于零是卖电，需要排除
            if buy_1['#1隔离变系统侧开关有功'].iloc[i] > 0:
                buy_1['#1隔离变系统侧开关有功'].iloc[i] = 0
            if buy_2['#2隔离变系统侧开关有功'].iloc[i] > 0:
                buy_2['#2隔离变系统侧开关有功'].iloc[i] = 0
        buy = pd.concat([self.data, buy_1 * 5 * 60 / 3600, buy_2 * 5 * 60 / 3600])
        buy.columns = ['DATATIME', '1号每五分钟买电量(KWh)', '2号买电量']
        return buy

    # 计算每五分钟中的总卖电量,单位是KWh
    def sell_total(self):
        sell_1 = self.df[['#1隔离变系统侧开关有功']] #有功小于零是买电，需要排除
        sell_2 = self.df[['#2隔离变系统侧开关有功']]
        if sell_1['#1隔离变系统侧开关有功'].iloc[i] < 0:
            sell_1['#1隔离变系统侧开关有功'].iloc[i] = 0
        if sell_2['#2隔离变系统侧开关有功'].iloc[i] < 0:
            sell_2['#2隔离变系统侧开关有功'].iloc[i] = 0
        sell = pd.concat([self.data, sell_1 * 5 * 60 / 3600, sell_2 * 5 * 60 / 3600])
        sell.columns = ['DATATIME', '1号每五分钟卖电量(KWh)', '2号卖电量']
        return sell

    # 计算每五分钟中的总发电量，单位是KWh
    def generate_total(self):
        gen_1 = self.df[['G1_KWH 1#有功电度量']]  # 单位是KWh
        gen_2 = self.df[['G2_KWH 2#有功电度量']]  # 累计值的当前行 - 上一行为每五分钟消耗量
        gen_total = pd.concat([self.data, gen_1.diff(), gen_2.diff()], axis=1).loc[1:]
        gen_total.columns = ['DATATIME', '1号总发电量(KWh)', '2号总发电量']
        return gen_total