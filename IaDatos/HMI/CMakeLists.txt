cmake_minimum_required(VERSION 3.16)

project(SmartChair_HMI VERSION 0.1 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Qt6 REQUIRED COMPONENTS Quick Location Positioning)

qt_standard_project_setup(REQUIRES 6.8)

# Content of downloaded design from Figma to Qt or similar
if (EXISTS "${CMAKE_CURRENT_LIST_DIR}/importedcontent/CMakeLists.txt")
    add_subdirectory(${CMAKE_CURRENT_LIST_DIR}/importedcontent)
endif()

qt_add_executable(appSmartChair_HMI
    main.cpp
)

qt_add_qml_module(appSmartChair_HMI
    URI SmartChair_HMI


    QML_FILES

        Main.qml

        Screens/Home.qml

        Components/SpeedGauge.qml
        Components/DriveWidget.qml
        Components/BottomMenu.qml
        Components/BatteryWidget.qml
        Components/HealthWidget.qml
        Components/SystemWidget.qml
        Components/MenuButton.qml

        Screens/Camera.qml
        Screens/GPS.qml
        Screens/VoiceAI.qml
        Screens/System.qml
        Screens/Joystick.qml



    RESOURCES

        Assets/home.svg
        Assets/camera.svg
        Assets/gps.svg
        Assets/ai.svg
        Assets/settings.svg
        Assets/joystick.svg

)

# Qt for iOS sets MACOSX_BUNDLE_GUI_IDENTIFIER automatically since Qt 6.1.
# If you are developing for iOS or macOS you should consider setting an
# explicit, fixed bundle identifier manually though.
set_target_properties(appSmartChair_HMI PROPERTIES
#    MACOSX_BUNDLE_GUI_IDENTIFIER com.example.appSmartChair_HMI
    MACOSX_BUNDLE_BUNDLE_VERSION ${PROJECT_VERSION}
    MACOSX_BUNDLE_SHORT_VERSION_STRING ${PROJECT_VERSION_MAJOR}.${PROJECT_VERSION_MINOR}
    MACOSX_BUNDLE TRUE
    WIN32_EXECUTABLE TRUE
)

target_link_libraries(appSmartChair_HMI
    PRIVATE
    Qt6::Quick
    Qt6::Location
    Qt6::Positioning
)

install(TARGETS appSmartChair_HMI
    BUNDLE DESTINATION .
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)
