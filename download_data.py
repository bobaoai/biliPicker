# This is the main code interface, the api documentation is stored in the mairui_api_doc_1.txt that helps pull out the whole market information of Chinese stock market. 
# We are using this file's guidance to download the data and manage it in the local file. Let's start this step by step. What should we do this?

import json
import requests
import pandas as pd
import numpy as np
import os
import time
import datetime
import concurrent.futures
import threading
import time
import requests
import copy
class DataShelf():
    def __init__(self) -> None:
        """
        The class is use to manage the local data that should be imported into the database. 
        The credential is stored in the mairui_credential.txt file.
        The output file is stored in BiliData folder, that contains the stock price, the stock information, the market information and trader's positions.
        The stock information and the market information are updated every day, I'd like to update data tag for each stock.
        The stock company information and trader's positions are updated every week. I'd like to update data tag for each stock.
        """
        self.credentials = json.load(open('/Volumes/Work/mytool/mairui_credential.txt', 'r'))
        self.data_path = '/Volumes/Work/mytool/mairui_data/'
    
    def get_data_directory(self, thefile: str) -> str:
        """
        This function is used to get the data directory for each file.
        """
        return {'dn_info': f"{self.data_path}dn/", 
                'dq_info': f"{self.data_path}dq/", 
                "financial_info": f"{self.data_path}financial/", 
                "market_info": f"{self.data_path}market/", 
                "trader_info": f"{self.data_path}trader/"}[thefile]
        
    
        
class DownloadData(object):
    semaphore = threading.Semaphore(20)

    def __init__(self, data_shelf: DataShelf) -> None:
        self.__data_shelf = data_shelf
        self.__base_url = "http://api.mairui.club/"
        self.__license = self.__data_shelf.credentials['key']
        # self.output_path = '/Volumes/Work/mytool/mairui_data/'
        
    def download_all_stock_price_pipe(self):
        the_file = pd.read_excel("/Volumes/Work/mytool/wind_data/Book1.xlsx", header=1)
        the_code = [i.split('.')[0] for i in the_file.Code.values]
        import concurrent.futures
        the_stock_price_dq_dict = {}
        # the_stock_jjxs_dict = {}
        # the_stock_cwzy_dict = {}
        the_stock_price_dn_dict = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=19) as executor:
            # Submit tasks to the thread pool
            stock_price_dq = {executor.submit(self.get_stock_fsjy, i, 'dq'): i for i in the_code}
            stock_price_dn = {executor.submit(self.get_stock_fsjy, i, 'dn'): i for i in the_code}
            
            # Collect the results as they become available
            for stock in concurrent.futures.as_completed(stock_price_dq):
                print(stock)
                stock_code = stock_price_dq[stock]
                try:
                    data = stock.result()
                    # the_stock_price_dq_dict[stock_code] = data
                    json.dump(data, open(f"{self.__data_shelf.get_data_directory(thefile='dq_info')}{stock_code}.json", 'w'))
                    print("outputed the stock price data for stock code:", stock_code)
                except Exception as exc:
                    print('Exception occurred while getting data for stock code:', stock_code, 'Exception:', exc)
            
            for stock in concurrent.futures.as_completed(stock_price_dn):
                stock_code = stock_price_dn[stock]
                try:
                    data = stock.result()
                    # the_stock_price_dn_dict[stock_code] = data
                    json.dump(data, open(f"{self.__data_shelf.get_data_directory(thefile='dn_info')}{stock_code}.json", 'w'))
                    print("outputed the stock price data for stock code:", stock_code)
                except Exception as exc:
                    print('Exception occurred while getting data for stock code:', stock_code, 'Exception:', exc)    


    def get_stock_list(self):
        """
        This function is used to get the stock list from the mairui api. 
        """
        url = self.__base_url + 'hslt/list/' + self.__license
        # calculate the spend time
        time = datetime.datetime.now()
        r = requests.get(url)
        r.raise_for_status()
        time1 = datetime.datetime.now()
        print('The time spend is: ', time1 - time)
        return r.json()
    
    # 3. 指数、行业、概念
    def get_index_list(self):
        """
        3. 指数、行业、概念
        API接口：http://api.mairui.club/hszg/list/您的licence
        备用接口：http://api1.mairui.club/hszg/list/您的licence
        接口说明：获取指数、行业、概念（包括基金，债券，美股，外汇，期货，黄金等的代码），其中isleaf为1（叶子节点）的记录的code（代码）可以作为下方接口的参数传入，从而得到某个指数、行业、概念下的相关股票。
        数据更新：每周六03:00更新
        请求频率：1分钟20次
        返回格式：标准Json格式      [{},...{}]
        字段名称	数据类型	字段说明
        code	string	代码
        name	string	名称
        type1	number	一级分类（0:A股,1:创业板,2:科创板,3:基金,4:香港股市,5:债券,6:美国股市,7:外汇,8:期货,9:黄金,10:英国股市）
        type2	number	二级分类（0:A股-申万行业,1:A股-申万二级,2:A股-热门概念,3:A股-概念板块,4:A股-地域板块,5:A股-证监会行业,6:A股-分类,7:A股-指数成分,8:A股-风险警示,9:A股-大盘指数,10:A股-次新股,11:A股-沪港通,12:A股-深港通,13:基金-封闭式基金,14:基金-开放式基金,15:基金-货币型基金,16:基金-ETF基金净值,17:基金-ETF基金行情,18:基金-LOF基金行情,21:基金-科创板基金,22:香港股市-恒生行业,23:香港股市-全部港股,24:香港股市-热门港股,25:香港股市-蓝筹股,26:香港股市-红筹股,27:香港股市-国企股,28:香港股市-创业板,29:香港股市-指数,30:香港股市-A+H,31:香港股市-窝轮,32:香港股市-ADR,33:香港股市-沪港通,34:香港股市-深港通,35:香港股市-中华系列指数,36:债券-沪深债券,37:债券-深市债券,38:债券-沪市债券,39:债券-沪深可转债,40:美国股市-中国概念股,41:美国股市-科技类,42:美国股市-金融类,43:美国股市-制造零售类,44:美国股市-汽车能源类,45:美国股市-媒体类,46:美国股市-医药食品类,48:外汇-基本汇率,49:外汇-热门汇率,50:外汇-所有汇率,51:外汇-交叉盘汇率,52:外汇-美元相关汇率,53:外汇-人民币相关汇率,54:期货-全球期货,55:期货-中国金融期货交易所,56:期货-上海期货交易所,57:期货-大连商品交易所,58:期货-郑州商品交易所,59:黄金-黄金现货,60:黄金-黄金期货
        level	number	层级，从0开始，根节点为0，二级节点为1，以此类推
        pcode	string	父节点代码
        pname	string	父节点名称
        isleaf	number	是否为叶子节点，0：否，1：是        """
        url = self.__base_url + 'hszg/list/' + self.__license
        r = requests.get(url)
        r.raise_for_status()
        return r.json()

    def get_stock_zg_list(self):
        """4. 根据指数、行业、概念找相关股票
        API接口：http://api.mairui.club/hszg/gg/指数、行业、概念代码/您的licence
        备用接口：http://api1.mairui.club/hszg/gg/指数、行业、概念代码/您的licence
        接口说明：根据“指数、行业、概念树”接口得到的代码作为参数，得到相关的股票。
        数据更新：每周六03:00更新
        请求频率：1分钟20次
        返回格式：标准Json格式      [{},...{}]
        字段名称	数据类型	字段说明
        dm	string	代码（根据接口参数可能是A股股票代码，也可能是其他指数、行业、概念的股票代码）
        mc	string	名称（根据接口参数可能是A股股票代码，也可能是其他指数、行业、概念的股票名称）
        jys	string	交易所，sh表示上证，sz表示深证（如果返回的是A股的股票，那么有值，否则是null）
        根据股票找相关指数、行业、概念
        API接口：http://api.mairui.club/hszg/zg/股票代码(如000001)/您的licence
        备用接口：http://api1.mairui.club/hszg/zg/股票代码(如000001)/您的licence
        接口说明：根据《股票列表》得到的股票代码作为参数，得到相关的指数、行业、概念。
        数据更新：每周六03:00更新
        请求频率：1分钟20次
        返回格式：标准Json格式      [{},...{}]
        字段名称	数据类型	字段说明
        code	string	指数、行业、概念代码，如：sw2_650300
        name	string	指数、行业、概念名称，如：沪深股市-申万二级-国防军工-地面兵装
        """
        url = self.__base_url + 'hszg/gg/' + self.__license
        r = requests.get(url)
        r.raise_for_status()
        return r.json()
        
    def get_stock_gsjj(self, stock_code):
        """
        API接口：http://api.mairui.club/hscp/gsjj/股票代码(如000001)/您的licence
        备用接口：http://api1.mairui.club/hscp/gsjj/股票代码(如000001)/您的licence
        接口说明：根据《股票列表》得到的股票代码获取上市公司的简介。包括公司基本信息，概念以及发行信息等。
        数据更新：每天15:30开始更新，次日凌晨3点前完成
        请求频率：1分钟20次
        返回格式：标准Json格式      [{},...{}]
        字段名称	数据类型	字段说明
        name	string	公司名称
        ename	string	公司英文名称
        market	string	上市市场
        idea	string	概念及板块，多个概念由英文逗号分隔
        ldate	string	上市日期，格式yyyy-MM-dd
        sprice	string	发行价格（元）
        principal	string	主承销商
        rdate	string	成立日期
        rprice	string	注册资本
        instype	string	机构类型
        organ	string	组织形式
        secre	string	董事会秘书
        phone	string	公司电话
        sphone	string	董秘电话
        fax	string	公司传真
        sfax	string	董秘传真
        email	string	公司电子邮箱
        semail	string	董秘电子邮箱
        site	string	公司网站
        post	string	邮政编码
        infosite	string	信息披露网址
        oname	string	证券简称更名历史
        addr	string	注册地址
        oaddr	string	办公地址
        desc	string	公司简介
        bscope	string	经营范围
        printype	string	承销方式
        referrer	string	上市推荐人
        putype	string	发行方式
        pe	string	发行市盈率（按发行后总股本）
        firgu	string	首发前总股本（万股）
        lastgu	string	首发后总股本（万股）
        realgu	string	实际发行量（万股）
        planm	string	预计募集资金（万元）
        realm	string	实际募集资金合计（万元）
        pubfee	string	发行费用总额（万元）
        collect	string	募集资金净额（万元）
        signfee	string	承销费用（万元）
        pdate	string	招股公告日"""
        url = self.__base_url + 'hscp/gsjj/' + stock_code + '/' + self.__license
        r = requests.get(url)
        r.raise_for_status()
        return r.json()

    def get_stock_sszs(self, stock_code):
        """
        Update monthly
        6. 所属指数
        API接口：http://api.mairui.club/hscp/sszs/股票代码(如000001)/您的licence
        备用接口：http://api1.mairui.club/hscp/sszs/股票代码(如000001)/您的licence
        接口说明：根据《股票列表》得到的股票代码获取上市公司的所属指数。
        数据更新：每天15:30开始更新，次日凌晨3点前完成
        请求频率：1分钟20次
        返回格式：标准Json格式      [{},...{}]
        字段名称	数据类型	字段说明
        mc	string	指数名称
        dm	string	指数代码
        ind	string	进入日期yyyy-MM-dd
        outd	string	退出日期yyyy-MM-dd"""
        url = self.__base_url + 'hscp/sszs/' + stock_code + '/' + self.__license
        r = requests.get(url)
        r.raise_for_status()
        return r.json()
    
    #7.历届高管成员
    def get_stock_ljgg(self, stock_code):
        """
        Update monthly
        7.历届高管成员
        API接口：http://api.mairui.club/hscp/ljgg/股票代码(如000001)/您的licence
        备用接口：http://api1.mairui.club/hscp/ljgg/股票代码(如000001)/您的licence
        接口说明：根据《股票列表》得到的股票代码获取上市公司的历届高管成员名单。
        数据更新：每天15:30开始更新，次日凌晨3点前完成
        请求频率：1分钟20次
        返回格式：标准Json格式      [{},...{}]
        字段名称	数据类型	字段说明
        name	string	姓名
        title	string	职务
        sdate	string	起始日期yyyy-MM-dd
        edate	string	终止日期yyyy-MM-dd
        """
        url = self.__base_url + 'hscp/ljgg/' + stock_code + '/' + self.__license
        r = requests.get(url)
        return r.json()
    
    def get_stock_ljds(self, stock_code):
        """
        8.历届董事会成员
        API接口：http://api.mairui.club/hscp/ljds/股票代码(如000001)/您的licence
        备用接口：http://api1.mairui.club/hscp/ljds/股票代码(如000001)/您的licence
        接口说明：根据《股票列表》得到的股票代码获取上市公司的历届董事会成员名单。
        数据更新：每天15:30开始更新，次日凌晨3点前完成
        请求频率：1分钟20次
        返回格式：标准Json格式      [{},...{}]
        字段名称	数据类型	字段说明
        name	string	姓名
        title	string	职务
        sdate	string	起始日期yyyy-MM-dd
        edate	string	终止日期yyyy-MM-dd
        """
        url = self.__base_url + 'hscp/ljds/' + stock_code + '/' + self.__license
        r = requests.get(url)
        return r.json()

    def get_stock_ljjj(self, stock_code):
        """
        9.历届监事会成员
        API接口：http://api.mairui.club/hscp/ljjj/股票代码(如000001)/您的licence
        备用接口：http://api1.mairui.club/hscp/ljjj/股票代码(如000001)/您的licence
        接口说明：根据《股票列表》得到的股票代码获取上市公司的历届监事会成员名单。
        数据更新：每天15:30开始更新，次日凌晨3点前完成
        请求频率：1分钟20次
        返回格式：标准Json格式      [{},...{}]
        字段名称	数据类型	字段说明
        name	string	姓名
        title	string	职务
        sdate	string	起始日期yyyy-MM-dd
        edate	string	终止日期yyyy-MM-dd"""
        url = self.__base_url + 'hscp/ljgg/' + stock_code + '/' + self.__license
        r = requests.get(url)
        return r.json()

    def get_stock_jnfh(self, stock_code):
        """10. 近年分红
        API接口：http://api.mairui.club/hscp/jnfh/股票代码(如000001)/您的licence
        备用接口：http://api1.mairui.club/hscp/jnfh/股票代码(如000001)/您的licence
        接口说明：根据《股票列表》得到的股票代码获取上市公司的近年来的分红实施结果。按公告日期倒序。
        数据更新：每天15:30开始更新，次日凌晨3点前完成
        请求频率：1分钟20次
        返回格式：标准Json格式      [{},...{}]
        字段名称	数据类型	字段说明
        sdate	string	公告日期yyyy-MM-dd
        give	string	每10股送股(单位：股)
        change	string	每10股转增(单位：股)
        send	string	每10股派息(税前，单位：元)
        line	string	进度
        cdate	string	除权除息日yyyy-MM-dd
        edate	string	股权登记日yyyy-MM-dd
        hdate	string	红股上市日yyyy-MM-dd
        """
        url = self.__base_url + 'hscp/jnfh/' + stock_code + '/' + self.__license
        r = requests.get(url)
        return r.json()
    
    def get_stock_jjxs(self, stock_code):
        """
        12. 解禁限售
        API接口：http://api.mairui.club/hscp/jjxs/股票代码(如000001)/您的licence
        备用接口：http://api1.mairui.club/hscp/jjxs/股票代码(如000001)/您的licence
        接口说明：根据《股票列表》得到的股票代码获取上市公司的解禁限售情况。按解禁日期倒序。
        数据更新：每天15:30开始更新，次日凌晨3点前完成
        请求频率：1分钟20次
        返回格式：标准Json格式      [{},...{}]
        字段名称	数据类型	字段说明
        rdate	string	解禁日期yyyy-MM-dd
        ramount	number	解禁数量(万股)
        rprice	number	解禁股流通市值(亿元)
        batch	number	上市批次
        pdate	string	公告日期yyyy-MM-dd
        """
        url = self.__base_url + 'hscp/jjxs/' + stock_code + '/' + self.__license
        r = requests.get(url)
        r.raise_for_status()
        return r.json()
    
    def get_stock_cwzy(self, stock_code):
        """13. 财务摘要
        API接口：http://api.mairui.club/hscp/cwzy/股票代码(如000001)/您的licence
        备用接口：http://api1.mairui.club/hscp/cwzy/股票代码(如000001)/您的licence
        接口说明：根据《股票列表》得到的股票代码获取上市公司历年的财务摘要。按截止日期倒序。
        数据更新：每天15:30开始更新，次日凌晨3点前完成
        请求频率：1分钟20次
        返回格式：标准Json格式      [{},...{}]
        字段名称	数据类型	字段说明
        date	string	截止日期yyyy-MM-dd
        sasset	string	每股净资产-摊薄/期末股数
        mflow	string	每股现金流
        fund	string	每股资本公积金
        fasset	string	固定资产合计
        flasset	string	流动资产合计
        total	string	资产总计
        debt	string	长期负债合计
        mainin	string	主营业务收入
        fee	string	财务费用
        profits	string	净利润
        """
        url = self.__base_url + 'hscp/cwzy/' + stock_code + '/' + self.__license
        r = requests.get(url)
        r.raise_for_status()
        return r.json()
    
    def get_stock_jdlr(self, stock_code):
        """14. 近一年各季度利润
        API接口：http://api.mairui.club/hscp/jdlr/股票代码(如000001)/您的licence
        备用接口：http://api1.mairui.club/hscp/jdlr/股票代码(如000001)/您的licence
        接口说明：根据《股票列表》得到的股票代码获取上市公司近一年各个季度的利润。按截止日期倒序。
        数据更新：每天15:30开始更新，次日凌晨3点前完成
        请求频率：1分钟20次
        返回格式：标准Json格式      [{},...{}]
        字段名称	数据类型	字段说明
        date	string	截止日期yyyy-MM-dd
        income	string	营业收入（万元）
        expend	string	营业支出（万元）
        profit	string	营业利润（万元）
        totalp	string	利润总额（万元）
        reprofit	string	净利润（万元）
        basege	string	基本每股收益(元/股)
        ettege	string	稀释每股收益(元/股)
        otherp	string	其他综合收益（万元）
        totalcp	string	综合收益总额（万元"""
        url = self.__base_url + 'hscp/jdlr/' + stock_code + '/' + self.__license
        r = requests.get(url)
        r.raise_for_status()
        return r.json()
    
    def get_stock_jdxj(self, stock_code):
        """15. 近一年各季度现金流
        API接口：http://api.mairui.club/hscp/jdxj/股票代码(如000001)/您的licence
        备用接口：http://api1.mairui.club/hscp/jdxj/股票代码(如000001)/您的licence
        接口说明：根据《股票列表》得到的股票代码获取上市公司近一年各个季度的现金流。按截止日期倒序。
        数据更新：每天15:30开始更新，次日凌晨3点前完成
        请求频率：1分钟20次
        返回格式：标准Json格式      [{},...{}]
        字段名称	数据类型	字段说明
        date	string	截止日期yyyy-MM-dd
        jyin	string	经营活动现金流入小计（万元）
        jyout	string	经营活动现金流出小计（万元）
        jyfinal	string	经营活动产生的现金流量净额（万元）
        tzin	string	投资活动现金流入小计（万元）
        tzout	string	投资活动现金流出小计（万元）
        tzfinal	string	投资活动产生的现金流量净额（万元）
        czin	string	筹资活动现金流入小计（万元）
        czout	string	筹资活动现金流出小计（万元）
        czfinal	string	筹资活动产生的现金流量净额（万元）
        hl	string	汇率变动对现金及现金等价物的影响（万元）
        cashinc	string	现金及现金等价物净增加额（万元）
        cashs	string	期初现金及现金等价物余额（万元）
        cashe	string	期末现金及现金等价物余额（万元）"""
        url = self.__base_url + 'hscp/jdxj/' + stock_code + '/' + self.__license
        r = requests.get(url)
        r.raise_for_status()
        return r.json()
    
    def get_stock_fsjy_test(self, stock_code, level):
        # Acquire the semaphore
        with self.semaphore:
            # Wait for 3 seconds to respect the API's rate limit
            time.sleep(3)
            
            # Call the API
            url = self.__base_url + 'hszbl/fsjy/' + stock_code + '/' + level + '/' + self.__license
            response = requests.get(url)
            
            # Check the response status and return the data
            # if response.status_code == 200:
            data = response.json()
            print(f"finished {stock_code} {level}")
            return data
            # else:
                # print('Failed to get data for stock code:', stock_code, 'Status code:', response.status_code)
                # return None
            
    def get_stock_fsjy(self, stock_code, level):
        """API接口：http://api.mairui.club/hszbl/fsjy/股票代码(如000001)/分时级别/您的licence
        备用接口：http://api1.mairui.club/hszbl/fsjy/股票代码(如000001)/分时级别/您的licence
        接口说明：根据《股票列表》得到的股票代码和分时级别获取历史交易数据，交易时间从远到近排序。目前 分时级别 支持5分钟、15分钟、30分钟、60分钟、日周月年级别（包括前后复权），
        对应的值分别是 5m（5分钟）、15m（15分钟）、30m（30分钟）、60m（60分钟）、dn(日线未复权)、dq（日线前复权）、dh（日线后复权）、wn(周线未复权)、
        wq（周线前复权）、wh（周线后复权）、mn(月线未复权)、mq（月线前复权）、mh（月线后复权）、yn(年线未复权)、yq（年线前复权）、yh（年线后复权） 。
        数据更新：分钟级别数据盘中更新，分时越小越优先更新，如5分钟级别会每5分钟更新，15分钟级别会每15分钟更新，以此类推，日线及以上级别每天16:00更新。
        请求频率：1分钟20次
        返回格式：标准Json格式      [{},...{}]
        字段名称	数据类型	字段说明
        d	string	交易时间，短分时级别格式为yyyy-MM-dd HH:mm:ss，日线级别为yyyy-MM-dd
        o	number	开盘价（元）
        h	number	最高价（元）
        l	number	最低价（元）
        c	number	收盘价（元）
        v	number	成交量（手）
        e	number	成交额（元）
        zf	number	振幅（%）
        hs	number	换手率（%）
        zd	number	涨跌幅（%）
        zde	number	涨跌额（元）
        """
        url = self.__base_url + 'hszbl/fsjy/' + stock_code + '/' + level + '/' + self.__license
        r = requests.get(url)
        r.raise_for_status()
        print(f"finished {stock_code} {level} {datetime.datetime.now()}")
        return r.json()
        
        
    def get_stock_kline(self, stock_code, kline_type):
        """
        This function is used to get the kline data of a stock. 
        """
        url = self.__base_url + 'hslt/kline/' + stock_code + '/' + kline_type + '/' + self.__license
        r = requests.get(url)
        r.raise_for_status()
        return r.json()
    
    def get_stock_kdj(self, stock_code, kline_type):
        """
        This function is used to get the kdj data of a stock. 
        """
        url = self.__base_url + 'hslt/kdj/' + stock_code + '/' + kline_type + '/' + self.__license
        r = requests.get(url)
        r.raise_for_status()
        return r.json()
    
    def get_stock_macd(self, stock_code, kline_type):
        """
        This function is used to get the macd data of a stock. 
        """
        url = self.__base_url + 'hslt/macd/' + stock_code + '/' + kline_type + '/' + self.__license
        r = requests.get(url)
        r.raise_for_status()
        return r.json()
    
    def get_stock_ma(self, stock_code, kline_type):
        """
        This function is used to get the ma data of a stock. 
        """
        url = self.__base_url + 'hslt/ma/' + stock_code + '/' + kline_type + '/' + self.__license
        r = requests.get(url)
        r.raise_for_status()
        return r.json()
    
    def get_stock_boll(self, stock_code, kline_type):
        """
        This function is used to get the boll data of a stock. 
        """
        url = self.__base_url + 'hslt/boll/' + stock_code + '/' + kline_type + '/' + self.__license
        r = requests.get(url)
        r.raise_for_status()
        return r.json()
    
    def get_stock_hsl(self, stock_code, kline_type):
        """
        This function is used to get the hsl data of a stock. 
        """
        url = self.__base_url + 'hslt/hsl/' + stock_code + '/' + kline_type + '/' + self.__license
        r = requests.get(url)
        r.raise_for_status()
        return r.json()
    

class ProcessData():
    """I am going to use this class to process the data downloaded from the API.
    I will use the closing price to calculate the MA, """
    def __init__(self, data_shelf):
        self.__data_shelf = data_shelf    
        
    def detect_yixianshengji(self, df):
        # Compute the 5-day moving average of the closing prices
        test_df = copy.deepcopy(df)
        test_df['CloseMA5'] = test_df['Close'].rolling(window=5).mean()

        # Check if the closing price is lower than the 5-day moving average for each day
        test_df['CloseBelowMA5'] = test_df['Close'] < test_df['CloseMA5']

        # For 5 days, check if all the values in this boolean series are True
        test_df['CloseBelowMA5For5Days'] = test_df['CloseBelowMA5'].rolling(window=5).sum() == 5

        # Compute the body of the candle as the absolute difference between the opening and closing prices
        test_df['Body'] = abs(test_df['Close'] - test_df['Open'])

        # Compute the lower shadow as the difference between the lower of the opening and closing prices and the lowest price
        test_df['LowerShadow'] = test_df[['Open', 'Close']].min(axis=1) - test_df['Low']

        # Check if the lower shadow is at least twice the length of the body of the candle
        test_df['LongLowerShadow'] = test_df['LowerShadow'] >= 2 * test_df['Body']

        # Combine the above conditions to detect the "一线生机" pattern
        df['Yixianshengji'] = test_df['CloseBelowMA5For5Days'] & test_df['LongLowerShadow']

        return df

    def signal_detect_pipe(self, stock_ticker, days=90):
        """load the json file 
        字段名称	数据类型	字段说明
        d	string	交易时间，短分时级别格式为yyyy-MM-dd HH:mm:ss，日线级别为yyyy-MM-dd
        o	number	开盘价（元）
        h	number	最高价（元）
        l	number	最低价（元）
        c	number	收盘价（元）
        v	number	成交量（手）
        e	number	成交额（元）
        zf	number	振幅（%）
        hs	number	换手率（%）
        zd	number	涨跌幅（%）
        zde	number	涨跌额（元）
        make the data into a pandas dataframe"""
        df = pd.DataFrame(json.load(open(f"{self.__data_shelf.get_data_directory(thefile='dq_info')}{stock_ticker}.json", 'r')))
        df['Close'] = df['c']
        df['Open'] = df['o']
        df['High'] = df['h']
        df['Low'] = df['l']
        df['Volume'] = df['number'] #test here to see if it works
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA10'] = df['Close'].rolling(window=10).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()
        df['AvgVolume20'] = df['Volume'].rolling(window=20).mean()

        last_ninty_days = df.tail(days)

        last_ninty_days = self.detect_chushuifurong(last_ninty_days)
        # Compute the average trading volume in the last 20 days
        last_ninty_days = self.detect_yixianshengji(last_ninty_days)
        last_ninty_days = self.detect_shuangfengguaner(last_ninty_days)
        last_ninty_days = self.detect_xianrenzhilu(last_ninty_days)
        # Check if the 'Yixianshengji' pattern occurred in the last forty trading days
        # yixianshengji_in_last_forty_days = last_forty_days['Yixianshengji'].any()
        # yixianshengji_in_last_forty_days
        
        
    def detect_chushuifurong(self, df):
        """For the "出水芙蓉" pattern with one day:

        Check if the 10-day moving average (MA) is less than the 20-day MA and the 20-day MA is less than the 60-day MA.
        The closing price of the previous day should be lower than the 10-day MA.
        The closing price of that day should be higher than the 60-day MA.
        The trading volume of that day should be more than twice the average trading volume in the last 20 days.
        For the "出水芙蓉" pattern with two days:

        Check if the 10-day moving average (MA) is less than the 20-day MA and the 20-day MA is less than the 60-day MA.
        The closing price of the day before the first day should be lower than the 5-day MA.
        After two consecutive rise days, the closing price of the second day needs to stand above the 60-day MA.
        The trading volume on both of these days should be more than twice the average trading volume in the last 20 days.      """

        # Prepare the conditions for the "出水芙蓉" pattern with one day
        cond1_1 = (df['MA10'].shift(1) < df['MA20'].shift(1)) & (df['MA20'].shift(1) < df['MA60'].shift(1))
        cond1_2 = (df['Close'].shift(1) < df['MA10'].shift(1)) or (df['Open'] < df['MA10'])
        cond1_3 = df['Close'] > df['MA60']
        cond1_4 = df['Volume'] > 2 * df['AvgVolume20']

        # Prepare the conditions for the "出水芙蓉" pattern with two days
        cond2_1 = (df['MA10'].shift(2) < df['MA20'].shift(2)) & (df['MA20'].shift(2) < df['MA60'].shift(2))
        cond2_2 = df['Close'].shift(2) < df['MA5'].shift(2)
        cond2_3 = df['Close'].shift(1) > df['Close'].shift(2)  # first rise day
        cond2_4 = df['Close'] > df['Close'].shift(1)  # second rise day
        cond2_5 = df['Close'] > df['MA60']
        cond2_6 = df['Volume'].shift(1) > 2 * df['AvgVolume20'].shift(1)
        cond2_7 = df['Volume'] > 2 * df['AvgVolume20']

        # Combine the conditions to detect the "出水芙蓉" pattern
        df['ChushuifurongOneDay'] = cond1_1 & cond1_2 & cond1_3 & cond1_4
        df['ChushuifurongTwoDays'] = cond2_1 & cond2_2 & cond2_3 & cond2_4 & cond2_5 & cond2_6 & cond2_7

        return df
    
    
    def detect_shuangfengguaner(self, df):
        """'双峰贯耳' Pattern:

            1. Identify a day (Day One) where the stock has the largest increase (closing price - opening price) in the last 20 days 
            and its closing price is above the maximum of the 5-day, 10-day, 30-day, and 60-day moving averages (MAs). Also, the 
            trading volume of Day One should be more than twice the average trading volume in the last 20 days.
            2. Within the next 30 trading days, before the second large increase happens, the 20-day MA should be above the maximum of 
            the 60-day and 30-day MAs while the 5-day MA is lower than the closing price of Day One. Also, the day should have the largest increase (closing price - opening price) after Day One.
            3. Within the 30 days after Day One, find a day where the price goes back to the closing price of Day One (within ±1%)."""
        test_df = copy.deepcopy(df)
        # Compute the moving averages
        test_df['MA5'] = test_df['Close'].rolling(window=5).mean()
        test_df['MA10'] = test_df['Close'].rolling(window=10).mean()
        test_df['MA20'] = test_df['Close'].rolling(window=20).mean()
        test_df['MA30'] = test_df['Close'].rolling(window=30).mean()
        test_df['MA60'] = test_df['Close'].rolling(window=60).mean()

        # Compute the average trading volume in the last 20 days
        test_df['AvgVolume20'] = test_df['Volume'].rolling(window=20).mean()

        # Compute the maximum moving average
        test_df['MaxMA'] = test_df[['MA5', 'MA10', 'MA30', 'MA60']].max(axis=1)

        # Compute the daily increase (closing price - opening price)
        test_df['Increase'] = test_df['Close'] - test_df['Open']
        test_df['LargestIncreaseIn20Days'] = test_df['Increase'].rolling(window=20).max()

        # Prepare the conditions for Day One
        cond1_1 = (test_df['Increase'] == test_df['LargestIncreaseIn20Days']) & (test_df['Close'] > test_df['MaxMA'])
        cond1_2 = test_df['Volume'] > 2 * test_df['AvgVolume20']
        test_df['DayOne'] = cond1_1 & cond1_2

        # Prepare the conditions for Day Two
        cond2_1 = test_df['MA20'] > test_df[['MA30', 'MA60']].max(axis=1)
        cond2_2 = test_df['MA5'] < test_df['Close'].shift()

        test_df['DayTwo'] = False
        for i in range(1, len(test_df)):
            if test_df['DayOne'].iloc[i-1] and cond2_1.iloc[i] and cond2_2.iloc[i]:
                test_df['DayTwo'].iloc[i] = True
                break

        # Check if the closing price goes back to the closing price of Day One within ±1%
        test_df['FinalDay'] = False
        for i in range(2, len(test_df)):
            if test_df['DayOne'].iloc[i-2] and test_df['DayTwo'].iloc[i-1]:
                if test_df['Close'].iloc[i] >= 0.99 * test_df['Close'].iloc[i-2]:
                    test_df['FinalDay'].iloc[i] = True

        # Final condition
        df['Shuangfengguaner'] = test_df['DayOne'] & test_df['DayTwo'].shift() & test_df['FinalDay'].shift(2)
        return df


    def detect_xianrenzhilu(self, df):
        # Compute the moving averages
        test_df = copy.deepcopy(df)
        test_df['MA5'] = test_df['Close'].rolling(window=5).mean()
        
        # Compute the upper shadow and the body of the candlestick
        test_df['UpperShadow'] = test_df['High'] - test_df['Close']
        test_df['Body'] = test_df['Close'] - test_df['Open']

        # Prepare the condition for the pattern
        df['Xianrenzhilu'] = ((test_df['Close'].shift(1) > test_df['MA5'].shift(1)) &
                            (test_df['Close'].shift(2) > test_df['MA5'].shift(2)) &
                            (test_df['Close'].shift(3) > test_df['MA5'].shift(3)) &
                            (test_df['Close'].shift(4) > test_df['MA5'].shift(4)) &
                            (test_df['Close'].shift(5) > test_df['MA5'].shift(5)) &
                            (test_df['UpperShadow'] > 1 * test_df['Body']) &
                            (test_df['Close'] > test_df['Open']) &
                            (test_df['Close'] > test_df['Close'].shift(1)))
        return df
    