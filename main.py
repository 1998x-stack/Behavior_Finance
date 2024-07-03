structure = {
    "00_发刊词": [
        "0.1_任何市场环境_你都能有机会"
    ],
    "01_模块一_什么是行为金融学": [
        "1.1_行为金融学为何擅长投资实战",
        "1.2_人是不是真的有智慧战胜市场",
        "1.3_价格错误是如何产生的",
        "1.4_现实生活中_你应该如何套利"
    ],
    "02_模块二_认知非理性": [
        "2.1_你能真正了解一家公司吗_信息收集阶段的认知偏差",
        "2.2_为什么股评不可信_信息加工阶段的认知偏差",
        "2.3_为什么人越自信赔得越多_信息输出阶段的认知偏差",
        "2.4_踩过的坑为什么还会踩_信息反馈阶段的认知偏差",
        "2.5_盈利和亏损得看参考点_参考点依赖"
    ],
    "03_模块三_决策非理性": [
        "3.1_牛市赚不到头_熊市一亏到底_盈利和亏损的不同风险偏好",
        "3.2_为何投资者总把小概率事件扩大化_错判概率导致的决策偏差",
        "3.3_为何不能天天查看自选股_狭隘框架",
        "3.4_做股票亏了无所谓而吃饭钱丢了可不行_心理账户理论",
        "3.5_股票市场就是个选美博弈_我得看你怎么选"
    ],
    "04_模块四_典型的交易错误": [
        "4.1_买熟悉的股票不对吗_分散化不足",
        "4.2_为什么把鸡蛋放在不同篮子里还是赔了_简单分散化",
        "4.3_来回倒腾为什么不如不动_过度交易理论",
        "4.4_卖出盈利的还是亏损的_卖出行为偏差",
        "4.5_涨停敢死队怎么赚钱的_买入行为偏差",
        "4.6_追逐热点投资对不对_羊群效应"
    ],
    "05_模块五_股票大盘的奥秘": [
        "5.1_大盘可以预测吗_大盘可预测理论",
        "5.2_无论如何你都应该买点股票_股权溢价之谜和战略资产配置",
        "5.3_怎样解读放量_价量关系理论1_Miller假说",
        "5.4_你参与了股票市场的击鼓传花_价量关系理论2_博傻理论"
    ],
    "06_模块六_行为投资策略": [
        "6.1_行为金融交易策略如何盈利_利用人们的错误",
        "6.2_为何会有免费的午餐_行为组合策略原理",
        "6.3_买大公司还是小公司的股票_规模溢价和价值溢价",
        "6.4_跌久必涨还是惯性效应_如何用好股价规律",
        "6.5_财报里藏了什么秘密_利用财务报表信息来制定交易策略",
        "6.6_免费的午餐一直都有_持续获得有效的投资策略"
    ],
    "07_模块七_实战分析": [
        "7.1_实战_贵州茅台的股票值得持有吗",
        "7.2_实战_从乐视网看公司基本面",
        "7.3_实战_股市大跌时如何应对",
        "7.4_实战_大盘短期能否预测",
        "7.5_实战_如何对待股权质押类资产",
        "7.6_实战_概念股炒作中_投资者怎么做",
        "7.7_实战_如何应对股市中的黑天鹅事件"
    ]
}


import os
from typing import Dict, Any

def create_directories_and_files(
        base_path: str, 
        structure: Dict[str, Any], 
        readme_file, 
        parent_path: str = "", 
        level: int = 1
    ):
    heading = "#" * level

    for key, value in structure.items():
        current_path = os.path.join(base_path, key.replace(" ", "_").replace("/", "_").replace("-", "_"))

        # 创建目录
        os.makedirs(current_path, exist_ok=True)

        # 在README中添加章节标题
        if parent_path:
            readme_file.write(f"{heading} {parent_path}/{key}\n\n")
        else:
            readme_file.write(f"{heading} {key}\n\n")

        # 递归调用创建子目录和文件
        if isinstance(value, dict) and value:
            create_directories_and_files(
                current_path, 
                value, 
                readme_file, 
                parent_path + "/" + key if parent_path else key, 
                level + 1
            )
        elif isinstance(value, list):
            for idx, item in enumerate(value):
                if isinstance(item, dict) and item:
                    create_directories_and_files(
                        current_path, 
                        item, 
                        readme_file, 
                        parent_path + "/" + key if parent_path else key, 
                        level + 1
                    )
                else:
                    item = f"{idx:02d}_{item}"
                    # file_name = item.replace(" ", "_").replace("/", "_").replace("-", "_") + ".py"
                    # file_path = os.path.join(current_path, file_name)
                    # with open(file_path, 'w', encoding='utf-8') as file:
                    #     file.write(f"# {item}\n\n")
                    #     file.write(f'"""\n\nLecture: {parent_path}/{key}\nContent: {item}\n\n"""\n\n')

                    # # 在README中添加文件链接
                    # item_clean = item.replace(" ", "_").replace("/", "_").replace("-", "_")
                    # parent_clean = parent_path.replace(" ", "_").replace("/", "_").replace("-", "_")
                    # key_clean = key.replace(" ", "_").replace("/", "_").replace("-", "_")
                    # readme_file.write(f"- [{item}](./{parent_clean}/{key_clean}/{item_clean}.py)\n")
                    
                    
                    file_name = item.replace(" ", "_").replace("/", "_").replace("-", "_") + ".md"
                    file_path = os.path.join(current_path, file_name)
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(f"# {item}\n\n")
                        file.write(f'"""\n\nLecture: {parent_path}/{key}\nContent: {item}\n\n"""\n\n')

                    # 在README中添加文件链接
                    item_clean = item.replace(" ", "_").replace("/", "_").replace("-", "_")
                    parent_clean = parent_path.replace(" ", "_").replace("/", "_").replace("-", "_")
                    key_clean = key.replace(" ", "_").replace("/", "_").replace("-", "_")
                    readme_file.write(f"- [{item}](./{parent_clean}/{key_clean}/{item_clean}.md)\n")
        else:
            # # 创建文件并写入初始内容
            # file_name = key.replace(" ", "_").replace("/", "_").replace("-", "_") + ".py"
            # file_path = os.path.join(current_path, file_name)
            # with open(file_path, 'w', encoding='utf-8') as file:
            #     file.write(f"# {key}\n\n")
            #     file.write(f'"""\n\nLecture: {parent_path}/{key}\nContent: {key}\n\n"""\n\n')

            # # 在README中添加文件链接
            # parent_clean = parent_path.replace(" ", "_").replace("/", "_").replace("-", "_")
            # key_clean = key.replace(" ", "_").replace("/", "_").replace("-", "_")
            # readme_file.write(f"- [{key}](./{parent_clean}/{key_clean}/{file_name})\n")
            
            
            file_name = key.replace(" ", "_").replace("/", "_").replace("-", "_") + ".md"
            file_path = os.path.join(current_path, file_name)
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(f"# {key}\n\n")
                file.write(f'"""\n\nLecture: {parent_path}/{key}\nContent: {key}\n\n"""\n\n')

            # 在README中添加文件链接
            parent_clean = parent_path.replace(" ", "_").replace("/", "_").replace("-", "_")
            key_clean = key.replace(" ", "_").replace("/", "_").replace("-", "_")
            readme_file.write(f"- [{key}](./{parent_clean}/{key_clean}/{file_name})\n")

        # 添加空行以分隔不同的章节
        readme_file.write("\n")

def main():
    root_dir = './'
    # 创建根目录
    os.makedirs(root_dir, exist_ok=True)

    # 创建 README.md 文件
    with open(os.path.join(root_dir, "README.md"), 'w', encoding='utf-8') as readme_file:
        readme_file.write("# 行为金融学\n\n")
        readme_file.write("这是一个关于行为金融学的目录结构。\n\n")
        create_directories_and_files(root_dir, structure, readme_file)

    print("目录和文件结构已生成，并创建 README.md 文件。")

if __name__ == "__main__":
    main()