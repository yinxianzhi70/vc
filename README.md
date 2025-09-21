## Vestiaire_product_auto_post_David

Vestiaire 电商产品自动填写程序，可以批量把 Vestiaire Collective Product Information.xlsx 里面的产品提交到 Vestiaire Collective 网站上。

## Instruction
1. 把产品信息填写到 Vestiaire Collective Product Information.xlsx 里面, 注意数据格式要和模板一样。

打开终端terminal,复制以下三列，点击回车键，开始运行

cd vc
source venv/bin/activate
python3 main.py

注意：

此时程序启动产品队列，有两种情况，
    - 如果 queue 文件夹里面已经有上次未处理完的产品文件，程序会接续上次的队列开始提交产品。
    - 如果 queue 文件夹为空，程序会把 Vestiaire Collective Product Information.xlsx 里面的产品拆开写入 queue 队列，并且将 Vestiaire Collective Product Information.xlsx 改名为 xxx - Pushed_To_Queue.xlsx。

    
3. 程序会自动打开一个 Chrome 浏览器，然后自动填写产品信息，自动下载图片到 download 文件夹，并填写产品图片表单。
4. 程序只会按步骤填写产品信息，不会提交产品，最后的草稿链接会保存到 result 文件夹里面。
5. 通过人工编辑打开草稿链接，检查并确认无误后，提交产品。

## 注意
- 在 result 里面的产品
- 提交产品后，如果有多余的不需要的草稿，请手动依次删除。
- 程序结束后，如果还残留有 Chrome 浏览器，请手动关闭。
- 你可以手动删除 queue 文件夹里面的文件，并将 Vestiaire Collective Product Information - xxx - Pushed_To_Queue.xlsx 改名回去，以重置队列，但注这样可能会有重复提交。
- 当程序在运行时，不要打开 .csv 结果文件，不然会与写入进程产生冲突，造成程序无法保存后续结果。

## Result 说明
- 程序会自动在结果里面加3个字段，分别是
    - Unfinished Steps: 产品提交时未完成的步骤。
    - Draft URL: 草稿超链接，人工编辑进入该链接，然后检查产品数据情况。
    - Error: 错误日志，看不懂后面可以再优化。
- 如果 Draft URL 没有带有 ID=，在第一步选择类别时就失败了，需要编辑手动检查类别。
- 更正类别后，可以把更正的产品数据从 Gender 列开始重新再粘贴到 Vestiaire Collective Product Information.xlsx 里面，然后重新运行 launch.bat 重新试一次。