#include <vector>
#include <variant>
#include <string>
#include <stdexcept>
#include <iostream>
#include <any>


struct IntArray {
    int64_t type_tag;  // 0 = int
    std::vector<int64_t> data;
};

extern "C" {
    IntArray* create_int_array(int64_t initial_size) {
        return new IntArray{0, std::vector<int64_t>(initial_size)};
    }

    void delete_int_array(IntArray* array) {
        delete array;
    }

    int64_t int_array_get(IntArray* array, int64_t index) {
        if (index < 0 || index >= array->data.size()) {
            throw std::out_of_range("Index out of bounds");
        }
        return array->data[index];
    }

    void int_array_set(IntArray* array, int64_t index, int64_t value) {
        if (index < 0 || index >= array->data.size()) {
            throw std::out_of_range("Index out of bounds");
        }
        array->data[index] = value;
    }

    // Get the size of the array
    int64_t int_array_size(IntArray* array) {
        return array->data.size();
    }
}


struct FloatArray {
    int64_t type_tag;  // 1 = float
    std::vector<float> data;
};

extern "C" {
    FloatArray* create_float_array(int64_t initial_size) {
        return new FloatArray{1, std::vector<float>(initial_size)};
    }

    void delete_float_array(FloatArray* array) {
        delete array;
    }

    float float_array_get(FloatArray* array, int64_t index) {
        if (index < 0 || index >= array->data.size()) {
            throw std::out_of_range("Index out of bounds");
        }
        return array->data[index];
    }

    void float_array_set(FloatArray* array, int64_t index, float value) {
        if (index < 0 || index >= array->data.size()) {
            throw std::out_of_range("Index out of bounds");
        }
        array->data[index] = value;
    }

    // Get the size of the array
    int64_t float_array_size(FloatArray* array) {
        return array->data.size();
    }
}


struct StringArray {
    int64_t type_tag;  // 2 = string
    std::vector<std::string> data;
};

extern "C" {
    StringArray* create_string_array(int64_t initial_size) {
        return new StringArray{2, std::vector<std::string>(initial_size)};
    }

    void delete_string_array(StringArray* array) {
        delete array;
    }

    const char* string_array_get(StringArray* array, int64_t index) {
        if (index < 0 || index >= array->data.size()) {
            throw std::out_of_range("Index out of bounds");
        }
        return array->data[index].c_str();
    }

    void string_array_set(StringArray* array, int64_t index, const char* value) {
        if (index < 0 || index >= array->data.size()) {
            throw std::out_of_range("Index out of bounds");
        }
        array->data[index] = std::string(value);
    }

    // Get the size of the array
    int64_t string_array_size(StringArray* array) {
        return array->data.size();
    }
}

struct BoolArray {
    int64_t type_tag;  // 3 = bool
    std::vector<bool> data;
};

extern "C" {
    BoolArray* create_bool_array(int64_t initial_size) {
        return new BoolArray{3, std::vector<bool>(initial_size)};
    }

    void delete_bool_array(BoolArray* array) {
        delete array;
    }

    bool bool_array_get(BoolArray* array, int64_t index) {
        if (index < 0 || index >= array->data.size()) {
            throw std::out_of_range("Index out of bounds");
        }
        return array->data[index];
    }

    void bool_array_set(BoolArray* array, int64_t index, bool value) {
        if (index < 0 || index >= array->data.size()) {
            throw std::out_of_range("Index out of bounds");
        }
        array->data[index] = value;
    }

    // Get the size of the array
    int64_t bool_array_size(BoolArray* array) {
        return array->data.size();
    }
}
