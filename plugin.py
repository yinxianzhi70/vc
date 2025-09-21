import os

from loguru import logger

from DrissionPage import ChromiumPage, ChromiumOptions


def set_2captcha(page):
    page.wait(5)
    for i in range(10):
        logger.debug("set 2captcha")

        twocaptcha_url = page.url.replace("options/options.html", "popup/popup.html")
        try:
            page.wait(1)
            page.get(twocaptcha_url)

            page.wait.ele_displayed('css:input[name=apiKey]', timeout=10, raise_err=True)
            page.wait(1)
            page('css:input[name=apiKey]').input('d1aba3d62b7a132461b8ce5eebe5d068')
            page.wait(1)
            page('css:button[class="default-btn"]').click()
            page('css:input[name=autoSolveRecaptchaV2]').wait.clickable(timeout=20, raise_err=True)
            logger.debug("2captcha setting in")
            page.wait(2)

            # open some auto-solvers
            # page('css:input[name=autoSubmitForms]').click()
            # page.wait(0.5)
            page('css:input[name=autoSolveRecaptchaV2]').click()
            page.wait(0.5)
            page('css:input[name=autoSolveRecaptchaV3]').click()
            page.wait(0.5)
            page('css:input[name=autoSolveHCaptcha]').click()
            page.wait(0.5)
            page('css:input[name=autoSolveGeetest]').click()
            page.wait(0.5)
            page('css:input[name=autoSolveTurnstile]').click()
            page.wait(1)
            break
        except Exception as e:
            logger.warning(e)
            continue
    logger.debug("set 2captcha done")


# 获取绝对地址
def init_chrome():
    co = ChromiumOptions()

    co.auto_port()
    co.set_argument('--window-size', '1920,1080')
    co.set_pref(arg='profile.default_content_settings.popups', value='0')
    co.set_timeouts(base=30)
    plugin_path = os.path.abspath('Captcha Solver_ Auto Recognition and Bypass 3.7.1')
    co.add_extension(plugin_path)

    page = ChromiumPage(addr_or_opts=co)

    set_2captcha(page)

    return page


if __name__ == '__main__':
    init_chrome()