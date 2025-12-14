# Unstloth Installation Windows

**Install NVIDIA Video Driver**

You should install the latest version of your GPUs driver. Download drivers here: [NVIDIA GPU Drive](https://www.nvidia.com/Download/index.aspx)

**Install Visual Studio C++**

You will need Visual Studio, with C++ installed. By default, C++ is not installed with Visual Studio, so make sure you select all of the C++ options. Also select options for Windows 10/11 SDK.

- Launch the Installer here:  [Visual Studio Community Edition](https://visualstudio.microsoft.com/vs/community/)
- In the installer, navigate to individual components and select all the options listed here:
  - **.NET Framework 4.8 SDK**
  - **.NET Framework 4.7.2 targeting pack**
  - **C# and Visual Basic Roslyn compilers**
  - **MSBuild**
  - **MSVC v143 - VS 2022 C++ x64/x86 build tools**
  - **C++ 2022 Redistributable Update**
  - **C++ CMake tools for Windows**
  - **C++/CLI support for v143 build tools (Latest)**
  - **MSBuild support for LLVM (clang-cl) toolset**
  - **C++ Clang Compiler for Windows (19.1.1)**
  - **Windows 11 SDK (10.0.22621.0)**
  - **Windows Universal CRT SDK**
  - **C++ 2022 Redistributable MSMs**

**Install CUDA Toolkit**

Follow the instructions to install [CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit-archive). 12.6.2

https://developer.nvidia.com/cuda-downloads?target_os=Windows&target_arch=x86_64&target_version=11&target_type=exe_local

Test it

```bash
nvidia-smi
nvcc --version
```

nvcc: NVIDIA (R) Cuda compiler driver
Copyright (c) 2005-2024 NVIDIA Corporation
Built on Thu_Sep_12_02:55:00_Pacific_Daylight_Time_2024
Cuda compilation tools, release 12.6, V12.6.77
Build cuda_12.6.r12.6/compiler.34841621_0



**Install Python & Create Environment**

**Activate Python Environment**

```
"D:\Alvaro\Training\TII - Generative AI\20240520 M2.4 - Finetuning\Capstone\.venv\Scripts\activate"
```

**Install Unsloth**

```
pip install "unsloth[windows] @ git+https://github.com/unslothai/unsloth.git"
```

**Install PyTorch**

You will need the correct version of PyTorch that is compatible with your CUDA drivers, so make sure to select them carefully. [Install PyTorch](https://pytorch.org/get-started/locally/)

```
pip install torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cu126

```





```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
xformers 0.0.31.post1 requires torch==2.7.1, but you have torch 2.7.0+cu128 which is incompatible.

or

ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
torchvision 0.22.0+cu128 requires torch==2.7.0+cu128, but you have torch 2.7.1 which is incompatible.
torchaudio 2.7.0+cu128 requires torch==2.7.0+cu128, but you have torch 2.7.1 which is incompatible.
```

**Install Triton**

```
pip install -U "triton-windows<3.4"
```



**Issues**

- In the SFTConfig of SFTTrainer, set `dataset_num_proc=1` to avoid a crashing issue:

    ```
    from trl import SFTConfig, SFTTrainer
    trainer = SFTTrainer(
        model = model,
        tokenizer = tokenizer,
        train_dataset = dataset,
        dataset_text_field = "text",
        max_seq_length = max_seq_length,
        packing = False, # Can make training 5x faster for short sequences.
        args = SFTConfig(
            dataset_num_proc=1, # HERE!!!
        ...
    )
    ```

- in `logging_utils.py` line 17:

  ```
  with open(filename, "r", encoding="utf-8") as file: file = file.read()
  ```

  