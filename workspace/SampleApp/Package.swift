// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "SampleApp",
    version: "1.0.0",
    platforms: [
        .iOS(.v17),
    ],
    targets: [
        .executableTarget(
            name: "SampleApp",
            path: "Sources/SampleApp"
        ),
        .testTarget(
            name: "SampleAppTests",
            dependencies: ["SampleApp"],
            path: "Tests/SampleAppTests"
        ),
    ],
    dependencies: [
        .package(url: "https://github.com/apple/swift-argument-parser", from: "1.2.0"),
    ]
)