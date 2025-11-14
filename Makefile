# Variables
PYTHON = python
SCRIPTUM_COMPILER = scriptum.compiler
CODE_FILE = ./stdlib/tests/code.fun
DYLIB_NAME = libscriptum_runtime.dylib
FFI_DIR = ./ffi
LIB_DIR = $(FFI_DIR)/lib
BUILD_DIR = $(FFI_DIR)/build
BIN_DIR = ./bin

# Targets
all: build compile run

# Build the FFI library
build:
	mkdir -p $(BUILD_DIR)
	cd $(BUILD_DIR) && cmake .. && make
	mkdir -p $(LIB_DIR)
	mv $(BUILD_DIR)/$(DYLIB_NAME) $(LIB_DIR)

# Compile the code using the scriptum compiler
compile: clean build
	$(PYTHON) -m $(SCRIPTUM_COMPILER) $(CODE_FILE)

# Run the compiled code
run:
	export DYLD_LIBRARY_PATH=$(LIB_DIR):$$DYLD_LIBRARY_PATH $(BIN_DIR)/code

# Clean up build artifacts
clean:
	rm -rf $(BUILD_DIR) $(LIB_DIR) $(BIN_DIR)/*.ll $(BIN_DIR)/*.o $(BIN_DIR)/code

test:
	$(PYTHON) -m pytest tests