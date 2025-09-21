import json
import time
import os
import random
from dotenv import load_dotenv

from openai import OpenAI
from loguru import logger
from bs4 import BeautifulSoup

# Load environment variables from .env file
load_dotenv()

# 初始化OpenAI客户端
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def ChatGpt(org_name, names, prompt1, prompt2):
    """
    Use OpenAI API to find the best match, fallback to simple matching if API key is not available.
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.warning("OpenAI API key not found, using simple matching strategy")
        return simple_match(org_name, names)
    
    try:
        # Prepare the prompt
        prompt = f"""Given the original name '{org_name}', find the best match from these options: {', '.join(names)}.
        Consider the context and return the most appropriate option.
        {prompt1}
        {prompt2}
        Return only the exact name from the options list, nothing else."""
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that matches names to predefined options."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=50
        )
        
        # Extract the response
        result = response.choices[0].message.content.strip()
        
        # Validate the result
        if result in names:
            logger.debug(f'AI found match: {result}')
            return result
        else:
            logger.warning(f'AI returned invalid result: {result}, falling back to simple matching')
            return simple_match(org_name, names)
            
    except Exception as e:
        logger.error(f'Error using OpenAI API: {str(e)}, falling back to simple matching')
        return simple_match(org_name, names)

def simple_match(org_name, names):
    """
    Simple string matching implementation as fallback.
    """
    # Clean input
    org_name = org_name.strip().lower()
    names = [name.strip() for name in names if name.strip()]
    
    # If list is empty or only has "No Results Found"
    if not names or (len(names) == 1 and names[0] == 'No Results Found'):
        return 'No Results Found'
        
    # Try exact match
    for name in names:
        if name.lower() == org_name:
            logger.debug(f'Found exact match: {name}')
            return name
            
    # Try partial match
    for name in names:
        if org_name in name.lower() or name.lower() in org_name:
            logger.debug(f'Found partial match: {name}')
            return name
            
    # Default to 'Other' if available, otherwise first option
    if 'Other' in names:
        logger.debug('No match found, using Other')
        return 'Other'
    else:
        logger.debug('No match found, using first option')
        return names[0]


def smart_click(tab, mode, options_css_xpath, click_rule, org_name, prompt1='', prompt2=''):
    """
    智能点选相应的选项
    mode: select 和 click,有 select-options 这种和 li span 点击选择两种模式
    click_rule: 当 mode 为  select 模式时，不需要指定点击处的 xpath/css
    choose_rule: 里面需要被替换的部分用 {{replace_name}} 代替
    """
    main_note = tab.ele(options_css_xpath)
    name_list = main_note.text.split('\n')

    the_best_match = ai_compare_option(org_name, name_list, prompt1, prompt2)

    if the_best_match == 'No Results Found':
        # 当出现 No Results Found 时说明 Material Color Pattern 这种没有搜索到结果，那么就情况输入框，重新指定 Other 为其值
        if "data-component-id='subcategory'" in options_css_xpath:
            # Details-category 的要为复数
            the_best_match = 'Others'
        else:
            the_best_match = 'Other'

        logger.info(f'{org_name} - No Results Found, set to Other')
        clear_btn = options_css_xpath + "/../..//button[contains(@data-cy, '-dropdownIcon')]"
        tab.ele(clear_btn).click()
        tab.wait(1)

    if mode == 'select':
        # Select 的列表选择
        tab.ele(options_css_xpath).select.by_text(the_best_match)
    else:
        # ui li 或 其它列表方式的选择
        choose_rule = click_rule.replace('{replace_name}', the_best_match)
        try:
            tab.ele(choose_rule, timeout=1).click()
        except:
            logger.debug(f'click option {org_name} failed')
            tab.remove_ele(options_css_xpath)  # 上面选择失败，所以此处从页面上移除下拉列表
            tab.wait(1)

    return


def ai_compare_option(org_name, names, prompt1, prompt2):
    """
    使用人工智能去比较，然后返回最适合的名称
    """
    # 清理和标准化输入
    org_name = org_name.strip()
    names = [name.strip() for name in names if name.strip()]
    
    # 如果列表为空或只包含"No Results Found"
    if not names or (len(names) == 1 and names[0] == 'No Results Found'):
        return 'No Results Found'
        
    # 尝试精确匹配（不区分大小写）
    org_name_lower = org_name.lower()
    for name in names:
        if name.lower() == org_name_lower:
            logger.debug(f'找到精确匹配: {name}')
            return name
            
    # 如果有"No Results Found"但不是唯一选项
    if 'No Results Found' in names:
        return 'No Results Found'
        
    # 使用AI进行模糊匹配
    best_match_name = ChatGpt(org_name, names, prompt1=prompt1, prompt2=prompt2)
    
    # 验证AI返回的匹配结果
    if best_match_name and best_match_name in names:
        return best_match_name
    elif 'Other' in names:
        logger.warning(f'AI匹配结果无效，使用Other作为后备选项')
        return 'Other'
    else:
        logger.warning(f'AI匹配结果无效，使用第一个选项作为后备')
        return names[0]


if __name__ == '__main__':
    # Test cases for smart matching
    test_cases = [
        {
            'original': 'Maison Margiela',
            'options': ['Maison Margiela', 'Maison Margiela X Reebok', 'Other'],
            'prompt1': '',
            'prompt2': ''
        },
        {
            'original': 'Ankle Boots',
            'options': ['Boots', 'Ankle Boots', 'Chelsea Boots', 'Other'],
            'prompt1': '',
            'prompt2': ''
        }
    ]

    # Run test cases
    for test in test_cases:
        logger.info(f"Testing matching for: {test['original']}")
        result = ChatGpt(
            test['original'],
            test['options'],
            test['prompt1'],
            test['prompt2']
        )
        logger.info(f"Match result: {result}")
