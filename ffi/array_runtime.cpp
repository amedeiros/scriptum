#include <vector>
#include <string>
#include <stdexcept>
#include <iostream>

struct ScriptumArray {
    int64_t type_tag;  // 0 = int, 1 = float, 2 = bool, 3 = string, 4 = array of arrays
    void* data;  // Pointers to the actual data arrays
};


extern "C" {
    ScriptumArray* create_int_array(int64_t initial_size) {
        return new ScriptumArray{0, new std::vector<int64_t>(initial_size)};
    }

    ScriptumArray* create_int_array_from_value(int64_t value, int64_t size) {
        ScriptumArray* array = new ScriptumArray{0, new std::vector<int64_t>(size, value)};
        return array;
    }

    int64_t int_array_get(ScriptumArray* array, int64_t index) {
        if (array->type_tag != 0) throw std::runtime_error("Not an int array");
        auto* vec = static_cast<std::vector<int64_t>*>(array->data);
        
        if (index < 0 || index >= vec->size()) {
            throw std::out_of_range("Index out of bounds");
        }
        return (*vec)[index];
    }

    void int_array_set(ScriptumArray* array, int64_t index, int64_t value) {
        if (array->type_tag != 0) throw std::runtime_error("Not an int array");
        auto* vec = static_cast<std::vector<int64_t>*>(array->data);
        if (index < 0 || index >= vec->size()) {
            throw std::out_of_range("Index out of bounds");
        }
        (*vec)[index] = value;
    }

    void int_array_push_back(ScriptumArray* array, int64_t value) {
        auto* vec = static_cast<std::vector<int64_t>*>(array->data);
        vec->push_back(value);
    }

    // Get the size of the array
    int64_t int_array_size(ScriptumArray* array) {
        auto* vec = static_cast<std::vector<int64_t>*>(array->data);
        return vec->size();
    }

    int64_t int_array_remove(ScriptumArray* array, int64_t index) {
        if (array->type_tag != 0) throw std::runtime_error("Not an int array");
        auto* vec = static_cast<std::vector<int64_t>*>(array->data);
        if (index < 0 || index >= vec->size()) {
            throw std::out_of_range("Index out of bounds");
        }
        int64_t removed = (*vec)[index];
        vec->erase(vec->begin() + index);
        return removed;
    }

    int64_t int_array_pop(ScriptumArray* array) {
        if (array->type_tag != 0) throw std::runtime_error("Not an int array");
        auto* vec = static_cast<std::vector<int64_t>*>(array->data);
        if (vec->empty()) {
            throw std::out_of_range("Array is empty");
        }
        int64_t removed = vec->back();
        vec->pop_back();
        return removed;
    }

    void int_array_insert(ScriptumArray* array, int64_t index, int64_t value) {
        if (array->type_tag != 0) throw std::runtime_error("Not an int array");
        auto* vec = static_cast<std::vector<int64_t>*>(array->data);
        if (index < 0 || index > vec->size()) {
            throw std::out_of_range("Index out of bounds");
        }
        vec->insert(vec->begin() + index, value);
    }

    int64_t int_array_index_of(ScriptumArray* array, int64_t value) {
        if (array->type_tag != 0) throw std::runtime_error("Not an int array");
        auto* vec = static_cast<std::vector<int64_t>*>(array->data);
        for (size_t i = 0; i < vec->size(); ++i) {
            if ((*vec)[i] == value) {
                return i;
            }
        }
        return -1;  // Not found
    }

    bool int_array_equals(ScriptumArray* a, ScriptumArray* b) {
        if (a->type_tag != 0 || b->type_tag != 0) throw std::runtime_error("Not an int array");
        auto* vec_a = static_cast<std::vector<int64_t>*>(a->data);
        auto* vec_b = static_cast<std::vector<int64_t>*>(b->data);
        if (vec_a->size() != vec_b->size()) return false;
        for (size_t i = 0; i < vec_a->size(); ++i) {
            if ((*vec_a)[i] != (*vec_b)[i]) return false;
        }
        return true;
    }
}

extern "C" {
    ScriptumArray* create_float_array(int64_t initial_size) {
        return new ScriptumArray{1, new std::vector<float>(initial_size)};
    }

    ScriptumArray* create_float_array_from_value(float value, int64_t size) {
        ScriptumArray* array = new ScriptumArray{1, new std::vector<float>(size, value)};
        return array;
    }

    float float_array_get(ScriptumArray* array, int64_t index) {
        auto* vec = static_cast<std::vector<float>*>(array->data);
        if (index < 0 || index >= vec->size()) {
            throw std::out_of_range("Index out of bounds");
        }
        return (*vec)[index];
    }

    void float_array_set(ScriptumArray* array, int64_t index, float value) {
        auto* vec = static_cast<std::vector<float>*>(array->data);
        if (index < 0 || index >= vec->size()) {
            throw std::out_of_range("Index out of bounds");
        }
        (*vec)[index] = value;
    }

    void float_array_push_back(ScriptumArray* array, float value) {
        static_cast<std::vector<float>*>(array->data)->push_back(value);
    }

    // Get the size of the array
    int64_t float_array_size(ScriptumArray* array) {
        return static_cast<std::vector<float>*>(array->data)->size();
    }

    float float_array_remove(ScriptumArray* array, int64_t index) {
        auto* vec = static_cast<std::vector<float>*>(array->data);
        if (index < 0 || index >= vec->size()) {
            throw std::out_of_range("Index out of bounds");
        }

        float removed = (*vec)[index];
        vec->erase(vec->begin() + index);
        return removed;
    }

    float float_array_pop(ScriptumArray* array) {
        auto* vec = static_cast<std::vector<float>*>(array->data);
        if (vec->empty()) {
            throw std::out_of_range("Array is empty");
        }
        float removed = vec->back();
        vec->pop_back();
        return removed;
    }

    void float_array_insert(ScriptumArray* array, int64_t index, float value) {
        if (array->type_tag != 1) throw std::runtime_error("Not a float array");
        auto* vec = static_cast<std::vector<float>*>(array->data);
        if (index < 0 || index > vec->size()) {
            throw std::out_of_range("Index out of bounds");
        }
        vec->insert(vec->begin() + index, value);
    }

    int64_t float_array_index_of(ScriptumArray* array, float value) {
        auto* vec = static_cast<std::vector<float>*>(array->data);
        for (size_t i = 0; i < vec->size(); ++i) {
            if ((*vec)[i] == value) {
                return i;
            }
        }
        return -1;  // Not found
    }

    bool float_array_equals(ScriptumArray* a, ScriptumArray* b) {
        auto* vec_a = static_cast<std::vector<float>*>(a->data);
        auto* vec_b = static_cast<std::vector<float>*>(b->data);
        if (vec_a->size() != vec_b->size()) return false;
        for (size_t i = 0; i < vec_a->size(); ++i) {
            if ((*vec_a)[i] != (*vec_b)[i]) return false;
        }
        return true;
    }
}


extern "C" {
    ScriptumArray* create_bool_array(int64_t initial_size) {
        return new ScriptumArray{2, new std::vector<bool>(initial_size)};
    }

    ScriptumArray* create_bool_array_from_value(bool value, int64_t size) {
        ScriptumArray* array = new ScriptumArray{2, new std::vector<bool>(size, value)};
        return array;
    }

    bool bool_array_get(ScriptumArray* array, int64_t index) {
        auto* vec = static_cast<std::vector<bool>*>(array->data);
        if (index < 0 || index >= vec->size()) {
            throw std::out_of_range("Index out of bounds");
        }
        return (*vec)[index];
    }

    void bool_array_set(ScriptumArray* array, int64_t index, bool value) {
        auto* vec = static_cast<std::vector<bool>*>(array->data);
        if (index < 0 || index >= vec->size()) {
            throw std::out_of_range("Index out of bounds");
        }
        (*vec)[index] = value;
    }

    void bool_array_push_back(ScriptumArray* array, bool value) {
        auto* vec = static_cast<std::vector<bool>*>(array->data);
        vec->push_back(value);
    }

    // Get the size of the array
    int64_t bool_array_size(ScriptumArray* array) {
        auto* vec = static_cast<std::vector<bool>*>(array->data);
        return vec->size();
    }

    bool bool_array_remove(ScriptumArray* array, int64_t index) {
        auto* vec = static_cast<std::vector<bool>*>(array->data);
        if (index < 0 || index >= vec->size()) {
            throw std::out_of_range("Index out of bounds");
        }

        bool removed = (*vec)[index];
        vec->erase(vec->begin() + index);
        return removed;
    }

    bool bool_array_pop(ScriptumArray* array) {
        auto* vec = static_cast<std::vector<bool>*>(array->data);
        if (vec->empty()) {
            throw std::out_of_range("Array is empty");
        }
        bool removed = vec->back();
        vec->pop_back();
        return removed;
    }

    void bool_array_insert(ScriptumArray* array, int64_t index, bool value) {
        auto* vec = static_cast<std::vector<bool>*>(array->data);
        if (index < 0 || index > vec->size()) {
            throw std::out_of_range("Index out of bounds");
        }
        vec->insert(vec->begin() + index, value);
    }

    int64_t bool_array_index_of(ScriptumArray* array, bool value) {
        auto* vec = static_cast<std::vector<bool>*>(array->data);
        for (size_t i = 0; i < vec->size(); ++i) {
            if ((*vec)[i] == value) {
                return i;
            }
        }
        return -1;  // Not found
    }

    bool bool_array_equals(ScriptumArray* a, ScriptumArray* b) {
        auto* vec_a = static_cast<std::vector<bool>*>(a->data);
        auto* vec_b = static_cast<std::vector<bool>*>(b->data);
        if (vec_a->size() != vec_b->size()) return false;
        for (size_t i = 0; i < vec_a->size(); ++i) {
            if ((*vec_a)[i] != (*vec_b)[i]) return false;
        }
        return true;
    }
}


extern "C" {
    ScriptumArray* create_string_array(int64_t initial_size) {
        return new ScriptumArray{3, new std::vector<std::string>(initial_size)};
    }

    ScriptumArray* create_string_array_from_value(const char* value, int64_t size) {
        ScriptumArray* array = new ScriptumArray{3, new std::vector<std::string>(size, std::string(value))};
        return array;
    }

    const char* string_array_get(ScriptumArray* array, int64_t index) {
        auto* vec = static_cast<std::vector<std::string>*>(array->data);
        if (index < 0 || index >= vec->size()) {
            throw std::out_of_range("Index out of bounds");
        }
        return (*vec)[index].c_str();
    }

    void string_array_set(ScriptumArray* array, int64_t index, const char* value) {
        auto* vec = static_cast<std::vector<std::string>*>(array->data);
        if (index < 0 || index >= vec->size()) {
            throw std::out_of_range("Index out of bounds");
        }
        (*vec)[index] = std::string(value);
    }

    void string_array_push_back(ScriptumArray* array, const char* value) {
        auto* vec = static_cast<std::vector<std::string>*>(array->data);
        vec->push_back(std::string(value));
    }

    // Get the size of the array
    int64_t string_array_size(ScriptumArray* array) {
        auto* vec = static_cast<std::vector<std::string>*>(array->data);
        return vec->size();
    }

    const char* string_array_remove(ScriptumArray* array, int64_t index) {
        auto* vec = static_cast<std::vector<std::string>*>(array->data);
        if (index < 0 || index >= vec->size()) {
            throw std::out_of_range("Index out of bounds");
        }

        std::string removed = (*vec)[index];
        vec->erase(vec->begin() + index);
        // Return a copy of the removed string
        char* ret = new char[removed.size() + 1];
        std::strcpy(ret, removed.c_str());
        return ret;
    }

    const char* string_array_pop(ScriptumArray* array) {
        auto* vec = static_cast<std::vector<std::string>*>(array->data);
        if (vec->empty()) {
            throw std::out_of_range("Array is empty");
        }
        std::string removed = vec->back();
        vec->pop_back();
        // Return a copy of the removed string
        char* ret = new char[removed.size() + 1];
        std::strcpy(ret, removed.c_str());
        return ret;
    }

    void string_array_insert(ScriptumArray* array, int64_t index, const char* value) {
        auto* vec = static_cast<std::vector<std::string>*>(array->data);
        if (index < 0 || index > vec->size()) {
            throw std::out_of_range("Index out of bounds");
        }
        vec->insert(vec->begin() + index, std::string(value));
    }

    int64_t string_array_index_of(ScriptumArray* array, const char* value) {
        auto* vec = static_cast<std::vector<std::string>*>(array->data);
        std::string val_str(value);
        for (size_t i = 0; i < vec->size(); ++i) {
            if ((*vec)[i] == val_str) {
                return i;
            }
        }
        return -1;  // Not found
    }

    bool string_array_equals(ScriptumArray* a, ScriptumArray* b) {
        auto* vec_a = static_cast<std::vector<std::string>*>(a->data);
        auto* vec_b = static_cast<std::vector<std::string>*>(b->data);
        if (vec_a->size() != vec_b->size()) return false;
        for (size_t i = 0; i < vec_a->size(); ++i) {
            if ((*vec_a)[i] != (*vec_b)[i]) return false;
        }
        return true;
    }
}


extern "C" {
    ScriptumArray* create_array_array(int64_t initial_size) {
        return new ScriptumArray{4, new std::vector<void*>(initial_size)};
    }

    ScriptumArray* create_array_array_from_value(void* value, int64_t size) {
        ScriptumArray* array = new ScriptumArray{4, new std::vector<void*>(size, value)};
        return array;
    }

    void* array_array_get(ScriptumArray* array, int64_t index) {
        auto* vec = static_cast<std::vector<void*>*>(array->data);
        if (index < 0 || index >= vec->size()) {
            throw std::out_of_range("Index out of bounds");
        }
        return (*vec)[index];
    }

    void array_array_set(ScriptumArray* array, int64_t index, void* value) {
        auto* vec = static_cast<std::vector<void*>*>(array->data);
        if (index < 0 || index >= vec->size()) {
            throw std::out_of_range("Index out of bounds");
        }
        (*vec)[index] = value;
    }

    void array_array_push_back(ScriptumArray* array, void* value) {
        auto* vec = static_cast<std::vector<void*>*>(array->data);
        vec->push_back(value);
    }

    // Get the size of the array
    int64_t array_array_size(ScriptumArray* array) {
        auto* vec = static_cast<std::vector<void*>*>(array->data);
        return vec->size();
    }

    void* array_array_remove(ScriptumArray* array, int64_t index) {
        auto* vec = static_cast<std::vector<void*>*>(array->data);
        if (index < 0 || index >= vec->size()) {
            throw std::out_of_range("Index out of bounds");
        }

        auto* removed = (*vec)[index];
        vec->erase(vec->begin() + index);
        return removed;
    }

    void* array_array_pop(ScriptumArray* array) {
        auto* vec = static_cast<std::vector<void*>*>(array->data);
        if (vec->empty()) {
            throw std::out_of_range("Array is empty");
        }
        void* removed = vec->back();
        vec->pop_back();
        return removed;
    }

    void array_array_insert(ScriptumArray* array, int64_t index, void* value) {
        auto* vec = static_cast<std::vector<void*>*>(array->data);
        if (index < 0 || index > vec->size()) {
            throw std::out_of_range("Index out of bounds");
        }
        vec->insert(vec->begin() + index, value);
    }

    bool array_array_equals(ScriptumArray* a, ScriptumArray* b) {
        auto* vec_a = static_cast<std::vector<void*>*>(a->data);
        auto* vec_b = static_cast<std::vector<void*>*>(b->data);
        if (vec_a->size() != vec_b->size()) return false;
        for (size_t i = 0; i < vec_a->size(); ++i) {
            void* elem_a = (*vec_a)[i];
            void* elem_b = (*vec_b)[i];
            int64_t type_tag_a = *(int64_t*)elem_a;
            int64_t type_tag_b = *(int64_t*)elem_b;
            if (type_tag_a != type_tag_b) return false;
            switch (type_tag_a) {
                case 0: // IntArray
                    if (!int_array_equals((ScriptumArray*)elem_a, (ScriptumArray*)elem_b)) return false;
                    break;
                case 1: // FloatArray
                    if (!float_array_equals((ScriptumArray*)elem_a, (ScriptumArray*)elem_b)) return false;
                    break;
                case 2: // BoolArray
                    if (!bool_array_equals((ScriptumArray*)elem_a, (ScriptumArray*)elem_b)) return false;
                    break;
                case 3: // StringArray
                    if (!string_array_equals((ScriptumArray*)elem_a, (ScriptumArray*)elem_b)) return false;
                    break;
                case 4: // ArrayArray
                    if (!array_array_equals((ScriptumArray*)elem_a, (ScriptumArray*)elem_b)) return false;
                    break;
                default:
                    return false;
            }
        }
        return true;
    }

    int64_t array_array_index_of(ScriptumArray* array, void* value) {
        int64_t value_type_tag = *(int64_t*)value;
        auto* vec = static_cast<std::vector<void*>*>(array->data);
        for (size_t i = 0; i < vec->size(); ++i) {
            void* elem = (*vec)[i];
            int64_t elem_type_tag = *(int64_t*)elem;
            if (elem_type_tag != value_type_tag) continue;
            switch (elem_type_tag) {
                case 0: // IntArray
                    if (int_array_equals((ScriptumArray*)elem, (ScriptumArray*)value)) return i;
                    break;
                case 1: // FloatArray
                    if (float_array_equals((ScriptumArray*)elem, (ScriptumArray*)value)) return i;
                    break;
                case 2: // BoolArray
                    if (bool_array_equals((ScriptumArray*)elem, (ScriptumArray*)value)) return i;
                    break;
                case 3: // StringArray
                    if (string_array_equals((ScriptumArray*)elem, (ScriptumArray*)value)) return i;
                    break;
                case 4: // ArrayArray
                    if (array_array_equals((ScriptumArray*)elem, (ScriptumArray*)value)) return i;
                    break;
                default:
                    break;
            }
        }
        return -1;
    }
}


extern "C" {
    void delete_array(ScriptumArray* array) {
        delete array;
    }

    int64_t alen(void* array_ptr) {
        if (!array_ptr) {
            throw std::invalid_argument("Null pointer provided");
        }
        int64_t type_tag = *(int64_t*)array_ptr;
        switch (type_tag) {
            case 0:  // IntArray
                return int_array_size((ScriptumArray*)array_ptr);
            case 1:  // FloatArray
                return float_array_size((ScriptumArray*)array_ptr);
            case 2:  // BoolArray
                return bool_array_size((ScriptumArray*)array_ptr);
            case 3:  // StringArray
                return string_array_size((ScriptumArray*)array_ptr);
            case 4:  // ArrayArray
                return array_array_size((ScriptumArray*)array_ptr);
            default:
                throw std::invalid_argument("Unknown array type");
        }
    }

    void areverse(void* array_ptr) {
        if (!array_ptr) {
            throw std::invalid_argument("Null pointer provided");
        }
        int64_t type_tag = *(int64_t*)array_ptr;
        switch (type_tag) {
            case 0: {  // IntArray
                ScriptumArray* arr = (ScriptumArray*)array_ptr;
                auto* vec = static_cast<std::vector<int64_t>*>(arr->data);
                std::reverse(vec->begin(), vec->end());
                break;
            }
            case 1: {  // FloatArray
                ScriptumArray* arr = (ScriptumArray*)array_ptr;
                auto* vec = static_cast<std::vector<float>*>(arr->data);
                std::reverse(vec->begin(), vec->end());
                break;
            }
            case 2: {  // BoolArray
                ScriptumArray* arr = (ScriptumArray*)array_ptr;
                auto* vec = static_cast<std::vector<bool>*>(arr->data);
                std::reverse(vec->begin(), vec->end());
                break;
            }
            case 3: {  // StringArray
                ScriptumArray* arr = (ScriptumArray*)array_ptr;
                auto* vec = static_cast<std::vector<std::string>*>(arr->data);
                std::reverse(vec->begin(), vec->end());
                break;
            }
            case 4: {  // ArrayArray
                ScriptumArray* arr = (ScriptumArray*)array_ptr;
                auto* vec = static_cast<std::vector<void*>*>(arr->data);
                std::reverse(vec->begin(), vec->end());
                break;
            }
            default:
                throw std::invalid_argument("Unknown array type");
        }
    }

    void asort(void* array_ptr) {
        if (!array_ptr) {
            throw std::invalid_argument("Null pointer provided");
        }
        int64_t type_tag = *(int64_t*)array_ptr;
        switch (type_tag) {
            case 0: {  // IntArray
                ScriptumArray* arr = (ScriptumArray*)array_ptr;
                auto* vec = static_cast<std::vector<int64_t>*>(arr->data);
                std::sort(vec->begin(), vec->end());
                break;
            }
            case 1: {  // FloatArray
                ScriptumArray* arr = (ScriptumArray*)array_ptr;
                auto* vec = static_cast<std::vector<float>*>(arr->data);
                std::sort(vec->begin(), vec->end());
                break;
            }
            case 2: {  // BoolArray
                ScriptumArray* arr = (ScriptumArray*)array_ptr;
                auto* vec = static_cast<std::vector<bool>*>(arr->data);
                std::sort(vec->begin(), vec->end());
                break;
            }
            case 3: {  // StringArray
                ScriptumArray* arr = (ScriptumArray*)array_ptr;
                auto* vec = static_cast<std::vector<std::string>*>(arr->data);
                std::sort(vec->begin(), vec->end());
                break;
            }
            case 4: {  // ArrayArray
                ScriptumArray* arr = (ScriptumArray*)array_ptr;
                auto* vec = static_cast<std::vector<void*>*>(arr->data);
                std::sort(vec->begin(), vec->end());
                break;
            }
            default:
                throw std::invalid_argument("Sorting not supported for this array type");
        }
    }   

    void aclear(void* array_ptr) {
        if (!array_ptr) {
            throw std::invalid_argument("Null pointer provided");
        }
        int64_t type_tag = *(int64_t*)array_ptr;
        switch (type_tag) {
            case 0: {  // IntArray
                ScriptumArray* arr = (ScriptumArray*)array_ptr;
                auto* vec = static_cast<std::vector<int64_t>*>(arr->data);
                vec->clear();
                break;
            }
            case 1: { // FloatArray
                ScriptumArray* arr = (ScriptumArray*)array_ptr;
                auto* vec = static_cast<std::vector<float>*>(arr->data);
                vec->clear();
                break;
            }
            case 2: {  // BoolArray
                ScriptumArray* arr = (ScriptumArray*)array_ptr;
                auto* vec = static_cast<std::vector<bool>*>(arr->data);
                vec->clear();
                break;
            }
            case 3: {  // StringArray
                ScriptumArray* arr = (ScriptumArray*)array_ptr;
                auto* vec = static_cast<std::vector<std::string>*>(arr->data);
                vec->clear();
                break;
            }
            case 4: {  // ArrayArray
                ScriptumArray* arr = (ScriptumArray*)array_ptr;
                auto* vec = static_cast<std::vector<void*>*>(arr->data);
                vec->clear();
                break;
            }
            default:
                throw std::invalid_argument("Unknown array type");
        }
    }

    void pp_array(void* array_ptr) {
        if (!array_ptr) {
            std::cout << "Null array" << std::endl;
            return;
        }
        int64_t type_tag = *(int64_t*)array_ptr;
        switch (type_tag) {
            case 0: {  // IntArray
                ScriptumArray* arr = (ScriptumArray*)array_ptr;
                auto* vec = static_cast<std::vector<int64_t>*>(arr->data);
                std::cout << "[";
                for (size_t i = 0; i < vec->size(); ++i) {
                    std::cout << (*vec)[i];
                    if (i < vec->size() - 1) std::cout << ", ";
                }
                std::cout << "]" << std::endl;
                break;
            }
            case 1: {  // FloatArray
                ScriptumArray* arr = (ScriptumArray*)array_ptr;
                auto* vec = static_cast<std::vector<float>*>(arr->data);
                std::cout << "[";
                for (size_t i = 0; i < vec->size(); ++i) {
                    std::cout << (*vec)[i];
                    if (i < vec->size() - 1) std::cout << ", ";
                }
                std::cout << "]" << std::endl;
                break;
            }
            case 2: {  // BoolArray
                ScriptumArray* arr = (ScriptumArray*)array_ptr;
                auto* vec = static_cast<std::vector<bool>*>(arr->data);
                std::cout << "[";
                for (size_t i = 0; i < vec->size(); ++i) {
                    std::cout << ((*vec)[i] ? "true" : "false");
                    if (i < vec->size() - 1) std::cout << ", ";
                }
                std::cout << "]" << std::endl;
                break;
            }
            case 3: {  // StringArray
                ScriptumArray* arr = (ScriptumArray*)array_ptr;
                auto* vec = static_cast<std::vector<std::string>*>(arr->data);
                std::cout << "[";
                for (size_t i = 0; i < vec->size(); ++i) {
                    std::cout << "\"" << (*vec)[i] << "\"";
                    if (i < vec->size() - 1) std::cout << ", ";
                }
                std::cout << "]" << std::endl;
                break;
            }
            case 4: {  // ArrayArray
                ScriptumArray* arr = (ScriptumArray*)array_ptr;
                auto* vec = static_cast<std::vector<void*>*>(arr->data);
                std::cout << "[";
                for (size_t i = 0; i < vec->size(); ++i) {
                    pp_array((*vec)[i]);  // Recursively print nested arrays
                    if (i < vec->size() - 1) std::cout << ", ";
                }
                std::cout << "]" << std::endl;
                break;
            }
            default:
                std::cout << "Unknown array type" << std::endl;
        }
    }
}