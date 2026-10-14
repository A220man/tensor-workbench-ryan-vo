import Foundation
import ArgumentParser

@main
struct SampleApp: AsyncParsableCommand {
    static let configuration = CommandConfiguration(
        abstract: "A sample SwiftPM iOS app for tensor-workbench testing"
    )

    @Option(name: .shortAndLong, help: "Name to greet")
    var name: String = "World"

    mutating func run() async throws {
        print("Hello, \(name)!")
        print("SampleApp v1.0.0 running on \(ProcessInfo.processInfo.operatingSystemVersionString)")
    }
}