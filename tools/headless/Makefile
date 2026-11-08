CXXFLAGS ?= -O2 -g
BUILD ?= build

.PHONY: all clean
all: $(BUILD)/libaci_game_frame.so $(BUILD)/aci_frame.json

$(BUILD):
	mkdir -p "$@"

$(BUILD)/libaci_game_frame.so: layer.cpp publisher.hpp | $(BUILD)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -std=c++17 -Wall -Wextra -Werror -Wno-missing-field-initializers -fvisibility=hidden -fPIC -shared -pthread -o "$@" layer.cpp

$(BUILD)/aci_frame.json: aci_frame.json | $(BUILD)
	cp "$<" "$@"

clean:
	rm -f "$(BUILD)/libaci_game_frame.so" "$(BUILD)/aci_frame.json" "$(BUILD)/smoke"

.PHONY: smoke
smoke: all $(BUILD)/smoke

$(BUILD)/smoke: smoke.cpp | $(BUILD)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -std=c++17 -Wall -Wextra -Werror -Wno-missing-field-initializers -o "$@" "$<" -lvulkan -lxcb
