# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: sphinx
#       format_version: '1.1'
#       jupytext_version: 1.16.4
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

"""
.. _visual-interface:

可视化
=========================

AgentScope 支持包括 Gradio 和 AgentScope Studio 在内的可视化，以提高用户体验。

Gradio
~~~~~~~~~~~~~~~~~~~~~~

首先，请确保已安装完整版本的 AgentScope, 其中包含 Gradio 包。

.. code-block:: bash

    # From pypi
    pip install agentscope[full]

    # From source code
    cd agentscope
    pip install .[full]


之后，请确保您的应用程序被封装在一个 `main` 函数中。

.. code-block:: python

    from agentscope.agents import DialogAgent, UserAgent
    import agentscope


    def main():
        # Your code here
        agentscope.init(model_configs={
            "config_name": "my-qwen-max",
            "model_type": "dashscope_chat",
            "model_name": "qwen-max"
        })

        agent = DialogAgent(
            name="Alice,
            model_config_name="my-qwen-max",
            sys_prompt="You're a helpful assistant named Alice."
        )
        user = UserAgent(agent)

        msg = None
        while True:
            msg = agent(msg)
            msg = user(msg)
            if msg.content == "exit":
                break


然后在终端执行以下命令启动 Gradio UI:

.. code-block :: bash

    as_gradio {path_to_your_python_code}

最后，您可以访问 Gradio UI，如下所示:

.. image:: https://img.alicdn.com/imgextra/i1/O1CN0181KSfH1oNbfzjUAVT_!!6000000005213-0-tps-3022-1530.jpg
   :align: center
   :class: bordered-image

------------------------------

AgentScope Studio
~~~~~~~~~~~~~~~~~~

AgentScope Studio 是一个开源的 Web UI 工具包，用于构建和监控多智能体应用程序。它提供以下功能:

* **仪表板**: 一个用于监控正在运行的应用程序，查看、管理运行历史的界面。

* **工作站**: 一个拖拽式构建应用的低代码开发界面。

* **服务器管理器**: 一个用于管理大规模分布式应用的界面。

* **画廊**: 工作站中应用程序示例。(即将推出!)

.. _studio:

启动 AgentScope Studio
----------------------------

要启动 Studio,首先确保您已安装最新版本的 AgentScope。然后运行以下 Python 代码:

.. code-block:: python

    import agentscope
    agentscope.studio.init()

或者可以在终端中运行以下命令:

.. code-block :: python

    as_studio

之后，可以访问 http://127.0.0.1:5000 上的 AgentScope Studio，将显示以下页面：

.. image:: https://img.alicdn.com/imgextra/i3/O1CN01Xic0GQ1ZkJ4M0iD8F_!!6000000003232-0-tps-3452-1610.jpg
   :align: center
   :class: bordered-image

当然，也可以更改主机和端口，并通过提供以下参数链接到你的应用程序运行历史记录:

.. code-block:: python

    import agentscope

    agentscope.studio.init(
        host="127.0.0.1",          # AgentScope Studio的IP地址
        port=5000,                 # AgentScope Studio的端口号
        run_dirs = [               # 应用运行历史的文件目录
            "xxx/xxx/runs",
            "xxx/xxx/runs"
        ]
    )


仪表板
-----------------

仪表板是一个 Web 界面，用于监控您正在运行的应用程序并查看运行历史记录。


注意
^^^^^^^^^^^^^^^^^^^^^

目前，仪表板存在以下限制，我们正在努力改进。欢迎任何反馈、贡献或建议!

* 运行的应用程序和 AgentScope Studio 必须运行在同一台机器上，以保证"URL/路径一致性"。如果您想在其他机器上访问 AgentScope，您可以尝试通过在远程机器上运行以下命令来转发端口：

.. code-block :: bash

    # 假设 AgentScope 运行在{as_host}:{as_port}，远程机器的端口是{remote_machine_port}
    ssh -L {remote_machine_port}:{as_host}:{as_port} [{user_name}@]{as_host}

* 对于分布式应用程序，支持单机多进程模式，但尚不支持多机多进程模式。

注册应用程序
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

在启动 AgentScope Studio 后，可以通过在 `agentscope.init()` 中指定 `studio_url` 来注册正在运行的应用程序:

.. code-block:: python

    import agentscope

    agentscope.init(
        # ...
        project="xxx",
        name="xxx",
        studio_url="http://127.0.0.1:5000"    # AgentScope Studio的URL
    )

注册后，可以在仪表板中查看正在运行的应用程序。为了区分不同的应用程序，可以指定应用程序的项目和名称。

.. image:: https://img.alicdn.com/imgextra/i2/O1CN01zcUmuJ1I3OUXy1Q35_!!6000000000837-0-tps-3426-1718.jpg
   :align: center
   :class: bordered-image

单击状态为 `waiting` 的程序，即可进入执行界面。例如，下图显示了一个对话界面。

.. image:: https://img.alicdn.com/imgextra/i3/O1CN01sA3VUc1h7OLKVLfr3_!!6000000004230-0-tps-3448-1736.jpg
   :align: center
   :class: bordered-image


.. note:: 一旦注册了正在运行的应用程序,`agentscope.agents.UserAgent` 类中的输入操作将转移到 AgentScope Studio 的仪表板。

导入运行历史记录
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

在 AgentScope 中，运行历史记录默认保存在 `./runs` 目录中。如果您想在仪表板中查看这些运行历史记录，可以在 `agentscope.studio.init()` 中指定 `run_dirs` :


.. code-block:: python

    import agentscope

    agentscope.studio.init(
        run_dirs = ["xxx/runs"]
    )

"""
